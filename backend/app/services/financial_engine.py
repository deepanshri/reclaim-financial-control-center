import logging
import threading
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from app.models.domain import (
    BankCredit,
    EvidenceItem,
    Finding,
    Payment,
    RecoveryRequest,
    Refund,
    Settlement,
)
from app.services.data_repository import DataRepository, data_repository
from app.core.config import settings
from app.core.money import paise_to_inr
from app.db import operational as operational_store
from app.services.detectors import (
    BankCreditDetector,
    DuplicateRefundDetector,
    FeeAnomalyDetector,
    MissingSettlementDetector,
    ReferenceAnomalyAuditor,
    SettlementDiscrepancyDetector,
    UncreditedRefundDetector,
)

logger = logging.getLogger("reclaim.engine")

PERIOD_LABELS = {
    "2024_H1": "2024 H1 (Jan–Jun)",
    "2024_H2": "2024 H2 (Jul–Dec)",
    "2025_H1": "2025 H1 (Jan–Jun)",
    "2025_H2": "2025 H2 (Jul–Dec)",
    "2026_H1": "2026 H1 (Jan–Jun)",
    "2026_H2": "2026 H2 (Jul–Dec)",
}

PERIOD_RANGES = {
    "2024_H1": ("2024-01-01", "2024-06-30"),
    "2024_H2": ("2024-07-01", "2024-12-31"),
    "2025_H1": ("2025-01-01", "2025-06-30"),
    "2025_H2": ("2025-07-01", "2025-12-31"),
    "2026_H1": ("2026-01-01", "2026-06-30"),
    "2026_H2": ("2026-07-01", "2026-12-31"),
}


class FinancialEngine:
    """
    Core Financial Engine for Reclaim.
    Calculates exact aggregates, executes independent rule detectors,
    computes deterministic health scores, and generates period-consistent financial ledgers.
    """

    def __init__(self, repo: Optional[DataRepository] = None):
        self.repo = repo or data_repository
        self.fee_detector = FeeAnomalyDetector(self.repo)
        self.duplicate_refund_detector = DuplicateRefundDetector(self.repo)
        self.missing_settlement_detector = MissingSettlementDetector(self.repo)
        self.bank_credit_detector = BankCreditDetector(self.repo)
        self.settlement_discrepancy_detector = SettlementDiscrepancyDetector(self.repo)
        self.uncredited_refund_detector = UncreditedRefundDetector(self.repo)
        self.reference_auditor = ReferenceAnomalyAuditor(self.repo)
        self._findings_cache: Dict[str, List[Finding]] = {}
        self._periods_cache: Optional[List[Dict[str, Any]]] = None
        self._findings_lock = threading.Lock()
        self._period_findings_locks: Dict[str, threading.Lock] = {}
        self._warm_lock = threading.Lock()
        self._warm_started = False

    def _lock_for_period(self, p_key: str) -> threading.Lock:
        with self._findings_lock:
            lock = self._period_findings_locks.get(p_key)
            if lock is None:
                lock = threading.Lock()
                self._period_findings_locks[p_key] = lock
            return lock

    def rerun_period(self, period: str) -> None:
        self.repo.load(force_reload=True, period=period)
        prefix = f"{period}:"
        with self._findings_lock:
            self._findings_cache = {k: v for k, v in self._findings_cache.items() if not k.startswith(prefix)}
        self._periods_cache = None

    # -------------------------------------------------------------------------
    # Anomaly Detection & Findings
    # -------------------------------------------------------------------------

    def get_findings(
        self,
        period: Optional[str] = None,
        year: Optional[int] = None,
        status: Optional[str] = None,
    ) -> List[Finding]:
        """
        Executes all rule-based detectors on raw period records.
        """
        p_key = self.repo.normalize_period_key(period, year)
        unfiltered_key = f"{p_key}:*"
        cache_key = f"{p_key}:{status or '*'}"

        def cached_findings() -> Optional[List[Finding]]:
            if cache_key in self._findings_cache:
                return list(self._findings_cache[cache_key])
            if unfiltered_key in self._findings_cache:
                all_cached = list(self._findings_cache[unfiltered_key])
                if status is not None:
                    all_cached = [f for f in all_cached if f.status == status]
                    self._findings_cache[cache_key] = list(all_cached)
                return all_cached
            return None

        with self._findings_lock:
            hit = cached_findings()
            if hit is not None:
                return hit

        with self._lock_for_period(p_key):
            with self._findings_lock:
                hit = cached_findings()
                if hit is not None:
                    return hit

            started = time.perf_counter()
            all_findings: List[Finding] = []

            # 1. Fee Anomaly Detector
            fee_findings = self.fee_detector.detect(period=p_key, year=year)
            all_findings.extend(fee_findings)

            # 2. Duplicate Refund Detector
            dup_findings = self.duplicate_refund_detector.detect(period=p_key, year=year)
            all_findings.extend(dup_findings)

            # 3. Missing Settlement Detector
            miss_settl_findings = self.missing_settlement_detector.detect(period=p_key, year=year)
            all_findings.extend(miss_settl_findings)

            # 4. Bank Credit Missing Detector
            bank_findings = self.bank_credit_detector.detect(period=p_key, year=year)
            all_findings.extend(bank_findings)

            # 5. Settlement amount discrepancy (expected net vs actual payout)
            disc_findings = self.settlement_discrepancy_detector.detect(period=p_key, year=year)
            all_findings.extend(disc_findings)

            # 6. Uncredited customer refunds
            uncred_findings = self.uncredited_refund_detector.detect(period=p_key, year=year)
            all_findings.extend(uncred_findings)

            # 7. Reference Auditor (under-review items such as settlement delay)
            confirmed_ids = [f.finding_id for f in all_findings]
            confirmed_types = [f.type for f in all_findings]
            ref_findings = self.reference_auditor.get_audited_reference_findings(
                confirmed_finding_ids=confirmed_ids,
                confirmed_types=confirmed_types,
                period=p_key,
                year=year,
            )
            all_findings.extend(ref_findings)

            with self._findings_lock:
                self._findings_cache[unfiltered_key] = list(all_findings)
                if status is not None:
                    filtered = [f for f in all_findings if f.status == status]
                    self._findings_cache[cache_key] = list(filtered)
                    all_findings = filtered

            logger.info(
                "financial engine findings period=%s elapsed=%.0fms findings=%d",
                p_key,
                (time.perf_counter() - started) * 1000,
                len(self._findings_cache[unfiltered_key]),
            )
            return list(all_findings)

    def get_finding_by_id(self, finding_id: str, period: Optional[str] = None) -> Optional[Finding]:
        all_findings = self.get_findings(period=period)
        for f in all_findings:
            if f.finding_id == finding_id:
                return f
        # Search all periods if not found
        for p_key in ["2026_H2", "2026_H1", "2025_H2", "2025_H1", "2024_H2", "2024_H1"]:
            for f in self.get_findings(period=p_key):
                if f.finding_id == finding_id:
                    return f
        return None

    def get_evidence_for_finding(self, finding_id: str, period: Optional[str] = None) -> List[EvidenceItem]:
        finding = self.get_finding_by_id(finding_id, period=period)
        if finding:
            return finding.evidence
        return []

    # -------------------------------------------------------------------------
    # Financial Totals & Health Score
    # -------------------------------------------------------------------------

    def get_financial_status(self, period: Optional[str] = None, year: Optional[int] = None) -> Dict[str, Any]:
        """
        Calculates exact monetary aggregates across payments, fees, refunds,
        settlements, losses, and recoveries for the selected period.
        """
        started = time.perf_counter()
        p_key = self.repo.normalize_period_key(period, year)

        payments = self.repo.get_all_payments(period=p_key, year=year)
        refunds = self.repo.get_all_refunds(period=p_key, year=year)
        settlements = self.repo.get_all_settlements(period=p_key, year=year)
        findings = self.get_findings(period=p_key, year=year)
        requests = self.get_recovery_requests(period=p_key)

        total_volume_paise = sum(p.amount_paise for p in payments)
        total_fees_paise = sum(p.fee_paise for p in payments)
        total_refunds_paise = sum(r.amount_paise for r in refunds)
        total_settlements_paise = sum(s.amount_paise for s in settlements)

        confirmed_findings = [f for f in findings if f.status == "confirmed"]
        under_review_findings = [f for f in findings if f.status == "under_review"]

        confirmed_loss_paise = sum(f.financial_impact_paise for f in confirmed_findings)
        confirmed_loss_inr = round(confirmed_loss_paise / 100.0, 2)

        recovery_requests_count = len(requests)
        recovery_requested_paise = sum(max(0, r.amount_requested_paise) for r in requests)

        recovered_paise = 0
        under_review_paise = 0
        not_recovered_paise = 0
        recovered_requests_count = 0
        under_review_count = 0
        not_recovered_count = 0

        for request in requests:
            status = (request.status or "").strip().lower()
            requested_paise = max(0, request.amount_requested_paise)
            recovered_amt = max(0, min(request.amount_recovered_paise, requested_paise))
            remainder_paise = requested_paise - recovered_amt

            if status in ("submitted", "pending", "under_review", "under review"):
                under_review_paise += requested_paise
                under_review_count += 1
            elif status in ("rejected", "not_recovered", "not recovered", "failed", "unrecovered"):
                not_recovered_paise += requested_paise
                not_recovered_count += 1
            elif status in ("resolved", "recovered"):
                recovered_paise += recovered_amt
                recovered_requests_count += 1
                if remainder_paise > 0:
                    not_recovered_paise += remainder_paise
            else:
                recovered_paise += recovered_amt
                if remainder_paise > 0:
                    not_recovered_paise += remainder_paise

        # Deterministic 3-tier Severity & Anomaly-Level Potential (Eligible) Recovery:
        # INR 0 – 99,999 -> MONITOR (Yellow)
        # INR 1,00,000 – 2,99,999 -> ACTION NEEDED (Orange)
        # INR 3,00,000+ -> URGENT ACTION (Red)
        if confirmed_loss_inr < 100000.0:
            severity_level = "healthy"
            severity_label = "MONITOR"
            severity_message = "A small difference was found, but no immediate action is needed."
            is_action = False
            review_status = "healthy"
        elif confirmed_loss_inr < 300000.0:
            severity_level = "needs_review"
            severity_label = "ACTION NEEDED"
            severity_message = "A meaningful amount is affected and should be reviewed."
            is_action = True
            review_status = "needs_review"
        else:
            severity_level = "action_needed"
            severity_label = "URGENT ACTION"
            severity_message = "A significant amount is affected and needs immediate attention."
            is_action = True
            review_status = "action_required"

        # Potential Recovery is independently derived from anomaly-level eligibility:
        # Sum of recoverable amounts across all eligible confirmed findings.
        potential_recovery_paise = sum(
            f.recoverable_amount_paise
            for f in confirmed_findings
            if f.is_recovery_eligible and f.recoverable_amount_paise > 0
        )

        # Deterministic Health Score
        health_score = self.calculate_health_score(
            total_volume_paise=total_volume_paise,
            confirmed_loss_paise=confirmed_loss_paise,
            confirmed_count=len(confirmed_findings),
            under_review_count=len(under_review_findings),
        )

        yr_int = int(p_key[:4]) if p_key else 2026
        start_date, end_date = PERIOD_RANGES.get(p_key, ("2024-01-01", "2026-12-31"))

        result = {
            "period": p_key,
            "period_label": PERIOD_LABELS.get(p_key, p_key),
            "period_start": start_date,
            "period_end": end_date,
            "year": yr_int,
            "currency": "INR",
            "total_payment_volume_inr": round(total_volume_paise / 100.0, 2),
            "total_fees_inr": round(total_fees_paise / 100.0, 2),
            "total_refunds_inr": round(total_refunds_paise / 100.0, 2),
            "total_settlements_inr": round(total_settlements_paise / 100.0, 2),
            "confirmed_loss_inr": confirmed_loss_inr,
            "money_affected_inr": confirmed_loss_inr,
            "potential_recovery_inr": round(potential_recovery_paise / 100.0, 2),
            # Compatibility alias of potential_recovery_inr. Not Money Affected.
            "potential_loss_inr": round(potential_recovery_paise / 100.0, 2),
            "recovery_requested_inr": round(recovery_requested_paise / 100.0, 2),
            "recovered_inr": round(recovered_paise / 100.0, 2),
            "recovery_requests_count": recovery_requests_count,
            "recovery_requested_amount": round(recovery_requested_paise / 100.0, 2),
            "recovered_requests_count": recovered_requests_count,
            "recovered_amount": round(recovered_paise / 100.0, 2),
            "under_review_count": under_review_count,
            "under_review_amount": round(under_review_paise / 100.0, 2),
            "under_review_inr": round(under_review_paise / 100.0, 2),
            "not_recovered_count": not_recovered_count,
            "not_recovered_amount": round(not_recovered_paise / 100.0, 2),
            "not_recovered_inr": round(not_recovered_paise / 100.0, 2),
            "confirmed_finding_count": len(confirmed_findings),
            "under_review_finding_count": len(under_review_findings),
            "total_finding_count": len(findings),
            "health_score": health_score,
            "severity_level": severity_level,
            "severity_label": severity_label,
            "severity_message": severity_message,
            "is_action_required": is_action,
            "review_status": review_status,
        }
        logger.info(
            "financial engine status period=%s elapsed=%.0fms",
            p_key,
            (time.perf_counter() - started) * 1000,
        )
        return result

    def calculate_health_score(
        self,
        total_volume_paise: int,
        confirmed_loss_paise: int,
        confirmed_count: int,
        under_review_count: int,
    ) -> int:
        """
        Deterministic Health Score formula (0-100):
        MONITOR periods with 0 confirmed findings = 100.
        Action periods deduct based on loss ratio and confirmed findings count.
        """
        if confirmed_count == 0 and confirmed_loss_paise == 0:
            return 100

        if total_volume_paise <= 0:
            return 100

        base_score = 100
        loss_ratio = confirmed_loss_paise / total_volume_paise
        loss_penalty = min(20, int(round(loss_ratio * 1000)))
        findings_penalty = min(24, confirmed_count * 8)
        review_penalty = min(10, under_review_count * 2)

        final_score = base_score - loss_penalty - findings_penalty - review_penalty
        return max(0, min(100, final_score))

    # -------------------------------------------------------------------------
    # Available Periods & Metadata
    # -------------------------------------------------------------------------

    def _period_summary_from_findings(self, p_key: str, findings: List[Finding]) -> Dict[str, Any]:
        confirmed = [f for f in findings if f.status == "confirmed"]
        confirmed_loss_paise = sum(f.financial_impact_paise for f in confirmed)
        confirmed_loss_inr = round(confirmed_loss_paise / 100.0, 2)
        start_date, end_date = PERIOD_RANGES.get(p_key, ("2024-01-01", "2026-12-31"))

        if confirmed_loss_inr < 100000.0:
            severity_level = "healthy"
            severity_label = "MONITOR"
            severity_message = "A small difference was found, but no immediate action is needed."
            is_action = False
            review_status = "healthy"
        elif confirmed_loss_inr < 300000.0:
            severity_level = "needs_review"
            severity_label = "ACTION NEEDED"
            severity_message = "A meaningful amount is affected and should be reviewed."
            is_action = True
            review_status = "needs_review"
        else:
            severity_level = "action_needed"
            severity_label = "URGENT ACTION"
            severity_message = "A significant amount is affected and needs immediate attention."
            is_action = True
            review_status = "action_required"

        return {
            "key": p_key,
            "label": PERIOD_LABELS.get(p_key, p_key),
            "year": int(p_key[:4]),
            "half": p_key[-2:],
            "start": start_date,
            "end": end_date,
            "review_status": review_status,
            "severity_level": severity_level,
            "severity_label": severity_label,
            "severity_message": severity_message,
            "is_action_required": is_action,
            "confirmed_finding_count": len(confirmed),
            "confirmed_loss_inr": confirmed_loss_inr,
        }

    def _period_catalog_stub(self, p_key: str) -> Dict[str, Any]:
        start_date, end_date = PERIOD_RANGES.get(p_key, ("2024-01-01", "2026-12-31"))
        return {
            "key": p_key,
            "label": PERIOD_LABELS.get(p_key, p_key),
            "year": int(p_key[:4]),
            "half": p_key[-2:],
            "start": start_date,
            "end": end_date,
            "review_status": "healthy",
            "severity_level": "healthy",
            "severity_label": "",
            "severity_message": "",
            "is_action_required": False,
            "confirmed_finding_count": 0,
            "confirmed_loss_inr": 0.0,
        }

    def get_available_periods(self, eager: bool = True) -> List[Dict[str, Any]]:
        """
        Evaluates period health for the period selector.

        eager=True computes findings for every period (used by /dataset/periods and tests).
        eager=False uses already-computed findings only so the first dashboard
        request is not blocked on the other five datasets.
        """
        if eager and self._periods_cache is not None:
            return list(self._periods_cache)

        order = ["2026_H2", "2026_H1", "2025_H2", "2025_H1", "2024_H2", "2024_H1"]
        periods_list: List[Dict[str, Any]] = []
        all_computed = True

        for p_key in order:
            cached = self._findings_cache.get(f"{p_key}:*")
            if cached is not None:
                periods_list.append(self._period_summary_from_findings(p_key, cached))
            elif eager:
                findings = self.get_findings(period=p_key)
                periods_list.append(self._period_summary_from_findings(p_key, findings))
            else:
                all_computed = False
                periods_list.append(self._period_catalog_stub(p_key))

        if all_computed:
            self._periods_cache = list(periods_list)
        return periods_list

    def schedule_background_warm(self, current_period: str) -> None:
        if settings.environment.lower() == "test":
            return
        with self._warm_lock:
            if self._warm_started:
                return
            self._warm_started = True
        thread = threading.Thread(
            target=self._warm_remaining_periods,
            args=(current_period,),
            daemon=True,
            name="reclaim-period-warm",
        )
        thread.start()

    def _warm_remaining_periods(self, current_period: str) -> None:
        # Let the first dashboard/anomalies/recovery burst finish before
        # competing for CPU and the CSV load lock.
        time.sleep(3.0)
        logger.info("Background warming remaining period indexes after %s", current_period)
        for p_key in ["2026_H2", "2026_H1", "2025_H2", "2025_H1", "2024_H2", "2024_H1"]:
            if p_key == current_period:
                continue
            try:
                started = time.perf_counter()
                self.get_findings(period=p_key)
                logger.info(
                    "Warmed period %s in %.0f ms",
                    p_key,
                    (time.perf_counter() - started) * 1000,
                )
            except Exception:
                logger.exception("Failed to warm period %s", p_key)
        self._periods_cache = None
        self.get_available_periods(eager=True)
        logger.info("Background period warming complete")

    # -------------------------------------------------------------------------
    # Recovery Requests
    # -------------------------------------------------------------------------

    def get_recovery_requests(self, period: Optional[str] = None, status: Optional[str] = None) -> List[RecoveryRequest]:
        p_key = self.repo.normalize_period_key(period)
        reqs = list(self.repo.get_recovery_requests(period=p_key))
        overlay = operational_store.list_recovery_requests(settings.demo_merchant_id, p_key)
        seen = {r.request_id for r in overlay}
        merged = overlay + [r for r in reqs if r.request_id not in seen]
        if status is not None:
            return [r for r in merged if r.status == status]
        return merged

    def get_recovery_request_by_id(self, request_id: str, period: Optional[str] = None) -> Optional[RecoveryRequest]:
        reqs = self.get_recovery_requests(period=period)
        for r in reqs:
            if r.request_id == request_id:
                return r
        for p_key in ["2026_H2", "2026_H1", "2025_H2", "2025_H1", "2024_H2", "2024_H1"]:
            for r in self.get_recovery_requests(period=p_key):
                if r.request_id == request_id:
                    return r
        return None

    # -------------------------------------------------------------------------
    # Statement Activity Ledger
    # -------------------------------------------------------------------------

    def get_statement_ledger(
        self,
        period: Optional[str] = None,
        year: Optional[int] = None,
        month: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int, Dict[str, Any]]:
        p_key = self.repo.normalize_period_key(period, year)
        yr_str = p_key[:4]
        half_str = p_key[-2:]
        if half_str == "H1":
            calendar_months = {f"{yr_str}-0{m}" for m in range(1, 7)}
        else:
            calendar_months = {f"{yr_str}-{m:02d}" for m in range(7, 13)}

        def ledger_status(date_str: str, base: str) -> str:
            # Keep the actual T+1/T+2 date. Reports stay on six calendar months.
            if date_str[:7] not in calendar_months:
                return f"{base} · T+1"
            return base

        payments = self.repo.get_all_payments(period=p_key, year=year)
        refunds = self.repo.get_all_refunds(period=p_key, year=year)
        settlements = self.repo.get_all_settlements(period=p_key, year=year)

        activity: List[Dict[str, Any]] = []

        for p in payments:
            if month and not p.created_date.startswith(month):
                continue
            activity.append({
                "id": f"act_pay_{p.id}",
                "date": p.created_date,
                "timestamp": p.created_at,
                "transaction_id": p.id,
                "type": "Payment",
                "status": "Settled" if p.captured else "Pending",
                "amount": p.amount_inr,
                "is_negative": False,
                "method": p.method,
            })
            if p.fee_paise > 0:
                activity.append({
                    "id": f"act_fee_{p.id}",
                    "date": p.created_date,
                    "timestamp": p.created_at,
                    "transaction_id": f"FEE-{p.id[-8:]}",
                    "type": "Fee",
                    "status": "Processed",
                    "fee_rate": f"{round(p.applied_fee_rate * 100, 2)}%",
                    "amount": p.fee_inr,
                    "is_negative": True,
                    "method": p.method,
                })

        for r in refunds:
            if month and not r.created_date.startswith(month):
                continue
            activity.append({
                "id": f"act_ref_{r.id}",
                "date": r.created_date,
                "timestamp": r.created_at,
                "transaction_id": r.id,
                "type": "Refund",
                "status": ledger_status(
                    r.created_date,
                    "Completed" if r.status == "processed" else "Pending",
                ),
                "amount": r.amount_inr,
                "is_negative": True,
                "method": "Refund",
            })

        for s in settlements:
            if month and not s.settlement_date.startswith(month):
                continue
            activity.append({
                "id": f"act_setl_{s.id}",
                "date": s.settlement_date,
                "timestamp": s.created_at,
                "transaction_id": s.id,
                "type": "Bank Deposit",
                "status": ledger_status(
                    s.settlement_date,
                    "Completed" if s.status == "processed" else "Processing",
                ),
                "amount": s.amount_inr,
                "is_negative": False,
                "method": "NEFT/RTGS",
            })

        activity.sort(key=lambda x: x["timestamp"], reverse=True)
        if search:
            needle = search.strip().lower()
            activity = [
                item
                for item in activity
                if needle in str(item.get("transaction_id", "")).lower()
                or needle in str(item.get("date", "")).lower()
                or needle in str(item.get("type", "")).lower()
            ]

        total_count = len(activity)
        start_idx = max(0, (page - 1) * page_size)
        end_idx = start_idx + page_size
        paginated_items = activity[start_idx:end_idx]

        kpi_volume_paise = sum(p.amount_paise for p in payments)
        kpi_fees_paise = sum(p.fee_paise for p in payments)
        kpi_settlements_paise = sum(s.amount_paise for s in settlements)
        payment_recon = [
            rec for rec in self.repo.get_all_settlement_recon(period=p_key)
            if rec.type == "payment"
        ]
        if payment_recon:
            matched = sum(1 for rec in payment_recon if rec.settled)
            kpi_matching_rate = round(100.0 * matched / len(payment_recon), 2)
        else:
            kpi_matching_rate = 100.0

        summary = {
            "total_payments_inr": paise_to_inr(kpi_volume_paise),
            "fees_deducted_inr": paise_to_inr(kpi_fees_paise),
            "bank_deposits_inr": paise_to_inr(kpi_settlements_paise),
            "matching_rate_percent": kpi_matching_rate,
        }

        return paginated_items, total_count, summary

    # -------------------------------------------------------------------------
    # Reporting & Monthly Breakdown
    # -------------------------------------------------------------------------

    def get_monthly_reports(self, period: Optional[str] = None, year: Optional[int] = None) -> List[Dict[str, Any]]:
        p_key = self.repo.normalize_period_key(period, year)

        payments = self.repo.get_all_payments(period=p_key, year=year)
        refunds = self.repo.get_all_refunds(period=p_key, year=year)
        settlements = self.repo.get_all_settlements(period=p_key, year=year)
        findings = self.get_findings(period=p_key, year=year)
        requests = self.get_recovery_requests(period=p_key)

        yr_str = p_key[:4] if p_key else str(year or 2026)
        half_str = p_key[-2:] if p_key else "H2"

        # Determine the exact 6 calendar months for this half-year
        if half_str == "H1":
            target_months = [f"{yr_str}-0{m}" for m in range(1, 7)]
        else:
            target_months = [f"{yr_str}-0{m}" if m < 10 else f"{yr_str}-{m}" for m in range(7, 13)]

        # Pre-populate all 6 target months
        monthly_map: Dict[str, Dict[str, Any]] = {
            m: {
                "volume_paise": 0,
                "fee_paise": 0,
                "refund_paise": 0,
                "settlement_paise": 0,
                "tx_count": 0,
                "refund_count": 0,
                "loss_paise": 0,
                "recovered_paise": 0,
            }
            for m in target_months
        }

        first_month = target_months[0]
        last_month = target_months[-1]

        def bound_month(mk: str) -> str:
            if mk in monthly_map:
                return mk
            if mk < first_month:
                return first_month
            return last_month

        for p in payments:
            mk = bound_month(p.created_date[:7])
            monthly_map[mk]["volume_paise"] += p.amount_paise
            monthly_map[mk]["fee_paise"] += p.fee_paise
            monthly_map[mk]["tx_count"] += 1

        for r in refunds:
            mk = bound_month(r.created_date[:7])
            monthly_map[mk]["refund_paise"] += r.amount_paise
            monthly_map[mk]["refund_count"] += 1

        for s in settlements:
            mk = bound_month(s.settlement_date[:7])
            monthly_map[mk]["settlement_paise"] += s.amount_paise

        for f in findings:
            mk = bound_month(f.start_date[:7])
            if f.status == "confirmed":
                monthly_map[mk]["loss_paise"] += f.financial_impact_paise

        for req in requests:
            if req.status.lower() in ["resolved", "recovered"] and req.resolved_date:
                mk = bound_month(req.resolved_date[:7])
                monthly_map[mk]["recovered_paise"] += req.amount_recovered_paise

        results: List[Dict[str, Any]] = []
        for month_key in target_months:
            data = monthly_map[month_key]
            results.append({
                "month": month_key,
                "transaction_count": data["tx_count"],
                "gross_volume_inr": round(data["volume_paise"] / 100.0, 2),
                "fees_inr": round(data["fee_paise"] / 100.0, 2),
                "refunds_inr": round(data["refund_paise"] / 100.0, 2),
                "settlements_inr": round(data["settlement_paise"] / 100.0, 2),
                "loss_detected_inr": round(data["loss_paise"] / 100.0, 2),
                "amount_recovered_inr": round(data["recovered_paise"] / 100.0, 2),
            })

        return results


# Singleton instance
financial_engine = FinancialEngine()
