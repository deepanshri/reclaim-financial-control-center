import csv
import json
import logging
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.config import settings
from app.core.exceptions import InvalidPeriodError
from app.core.money import inr_to_paise
from app.models.domain import (
    BankCredit,
    EvidenceItem,
    FeeContract,
    Payment,
    RecoveryRequest,
    Refund,
    Settlement,
    SettlementReconRecord,
)

logger = logging.getLogger("reclaim.repository")

PERIOD_KEYS = ["2024_H1", "2024_H2", "2025_H1", "2025_H2", "2026_H1", "2026_H2"]
DEFAULT_PERIOD = "2026_H2"


class PeriodStore:
    """Holds typed domain models for a single period."""

    def __init__(self, key: str):
        self.key = key
        self.meta: Dict[str, Any] = {}
        self.payments: List[Payment] = []
        self.payments_by_id: Dict[str, Payment] = {}
        self.refunds: List[Refund] = []
        self.refunds_by_id: Dict[str, Refund] = {}
        self.refunds_by_payment_id: Dict[str, List[Refund]] = {}
        self.settlements: List[Settlement] = []
        self.settlements_by_id: Dict[str, Settlement] = {}
        self.settlements_by_utr: Dict[str, Settlement] = {}
        self.settlement_recon: List[SettlementReconRecord] = []
        self.recon_by_payment_id: Dict[str, SettlementReconRecord] = {}
        self.bank_credits: List[BankCredit] = []
        self.bank_credits_by_settlement_id: Dict[str, BankCredit] = {}
        self.bank_credits_by_utr: Dict[str, BankCredit] = {}
        self.fee_contracts: List[FeeContract] = []
        self.recovery_requests: List[RecoveryRequest] = []
        self.reference_anomalies: List[Dict[str, Any]] = []
        self.reference_evidence: List[Dict[str, Any]] = []
        self.monthly_summary: List[Dict[str, Any]] = []


class DataRepository:
    """
    Centralized data repository that loads and normalizes raw dataset records
    into typed domain objects with exact integer paise monetary values across all 6 periods.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.data_dir = base_dir / "data" / "reclaim_six_half_year_datasets"
        else:
            self.data_dir = Path(data_dir)

        self._periods: Dict[str, PeriodStore] = {}
        self._loaded_periods: Set[str] = set()
        self._data_quality_issues: List[str] = []
        self._load_lock = threading.Lock()

    @property
    def is_loaded(self) -> bool:
        return bool(self._loaded_periods)

    def loaded_period_keys(self) -> List[str]:
        return [key for key in PERIOD_KEYS if key in self._loaded_periods]

    def period_keys(self) -> List[str]:
        found = [key for key in PERIOD_KEYS if (self.data_dir / key).is_dir()]
        return found or list(PERIOD_KEYS)

    def normalize_period_key(self, period: Optional[str] = None, year: Optional[int] = None) -> str:
        known = self.period_keys()

        if period:
            cleaned = period.strip().replace("-", "_").replace(" ", "_").upper()
            if cleaned in known:
                return cleaned
            for key in PERIOD_KEYS:
                if (key == cleaned or key.replace("_", "") == cleaned) and key in known:
                    return key
            raise InvalidPeriodError(period, known)

        if year is not None:
            yr_str = str(year)
            for key in (f"{yr_str}_H2", f"{yr_str}_H1"):
                if key in known:
                    return key
            raise InvalidPeriodError(str(year), known)

        if DEFAULT_PERIOD in known:
            return DEFAULT_PERIOD
        if known:
            return known[-1]
        return DEFAULT_PERIOD

    def ensure_period(self, period: Optional[str] = None, year: Optional[int] = None) -> str:
        key = self.normalize_period_key(period, year)
        with self._load_lock:
            self._load_period_unlocked(key)
        return key

    def load(self, force_reload: bool = False, period: Optional[str] = None) -> None:
        with self._load_lock:
            if period:
                key = self.normalize_period_key(period)
                self._load_period_unlocked(key, force_reload=force_reload)
                return
            for p_key in self.period_keys():
                self._load_period_unlocked(p_key, force_reload=force_reload)

    def _load_period_unlocked(self, p_key: str, force_reload: bool = False) -> None:
        if p_key in self._loaded_periods and not force_reload:
            return

        p_dir = self.data_dir / p_key
        if not p_dir.is_dir():
            raise InvalidPeriodError(p_key, self.period_keys())

        started = time.perf_counter()
        store = PeriodStore(p_key)

        # 1. Meta
        with (p_dir / "dataset_meta.json").open("r", encoding="utf-8") as f:
            store.meta = json.load(f)

        # 2. Fee Contracts
        with (p_dir / "fee_contracts.csv").open("r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                store.fee_contracts.append(
                    FeeContract(
                        contract_id=row["contract_id"],
                        merchant_id=row["merchant_id"],
                        provider=row["provider"],
                        fee_type=row["fee_type"],
                        contracted_rate=float(row["contracted_rate"]),
                        currency=row["currency"],
                        effective_from=row["effective_from"],
                        effective_to=row["effective_to"],
                        notes=row.get("notes", ""),
                    )
                )

        # 3. Payments
        with (p_dir / "payments.csv").open("r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                p_id = row["id"]
                created_ts = int(row["created_at"])
                dt_str = datetime.fromtimestamp(created_ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                date_str = dt_str[:10]
                year = int(date_str[:4])
                amt_paise = int(row["amount"])
                fee_paise = int(row["fee"])
                tax_paise = int(row["tax"])
                amt_ref_paise = int(row["amount_refunded"]) if row.get("amount_refunded") else 0

                p = Payment(
                    id=p_id,
                    amount_paise=amt_paise,
                    currency=row["currency"],
                    status=row["status"],
                    order_id=row.get("order_id", ""),
                    invoice_id=row.get("invoice_id", ""),
                    description=row.get("description", ""),
                    method=row.get("method", "upi"),
                    international=row.get("international", "false").lower() == "true",
                    refund_status=row.get("refund_status") if row.get("refund_status") != "null" else None,
                    amount_refunded_paise=amt_ref_paise,
                    captured=row.get("captured", "true").lower() in ["true", "1"],
                    email=row.get("email", ""),
                    contact=row.get("contact", ""),
                    fee_paise=fee_paise,
                    tax_paise=tax_paise,
                    created_at=created_ts,
                    created_at_dt=dt_str,
                    created_date=date_str,
                    created_year=year,
                    contract_fee_rate=float(row.get("contract_fee_rate", 0.018)),
                    applied_fee_rate=float(row.get("applied_fee_rate", 0.018)),
                    base_fee_inr=float(row.get("base_fee", 0.0)),
                    anomaly_type=row.get("anomaly_type", ""),
                )
                store.payments.append(p)
                store.payments_by_id[p_id] = p

        # 4. Refunds
        with (p_dir / "refunds.csv").open("r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                r_id = row["id"]
                pay_id = row["payment_id"]
                created_ts = int(row["created_at"])
                dt_str = datetime.fromtimestamp(created_ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                date_str = dt_str[:10]
                year = int(date_str[:4])
                amt_paise = int(row["amount"])

                r = Refund(
                    id=r_id,
                    payment_id=pay_id,
                    amount_paise=amt_paise,
                    currency=row["currency"],
                    created_at=created_ts,
                    created_at_dt=dt_str,
                    created_date=date_str,
                    created_year=year,
                    receipt=row.get("receipt", ""),
                    status=row.get("status", "processed"),
                    speed_requested=row.get("speed_requested", "normal"),
                    speed_processed=row.get("speed_processed", "normal"),
                    acquirer_utr=row.get("acquirer_utr", ""),
                    anomaly_type=row.get("anomaly_type", ""),
                    duplicate_of_refund_id=row.get("duplicate_of_refund_id", ""),
                )
                store.refunds.append(r)
                store.refunds_by_id[r_id] = r
                if pay_id not in store.refunds_by_payment_id:
                    store.refunds_by_payment_id[pay_id] = []
                store.refunds_by_payment_id[pay_id].append(r)

        # 5. Settlements
        with (p_dir / "settlements.csv").open("r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                s_id = row["id"]
                utr = row.get("utr", "")
                settl_date = row.get("settlement_date", "")
                settl_year = int(settl_date[:4]) if settl_date else int(p_key[:4])
                ref_adj_paise = inr_to_paise(row.get("refund_adjustment", 0))

                s = Settlement(
                    id=s_id,
                    amount_paise=int(row["amount"]),
                    status=row.get("status", "processed"),
                    fees_paise=int(row.get("fees", 0)),
                    tax_paise=int(row.get("tax", 0)),
                    utr=utr,
                    created_at=int(row.get("created_at", 0)),
                    settlement_date=settl_date,
                    settlement_year=settl_year,
                    payment_count=int(row.get("transaction_count", row.get("payment_count", 0))),
                    refund_adjustment_paise=ref_adj_paise,
                    anomaly_type=row.get("anomaly_type", ""),
                )
                store.settlements.append(s)
                store.settlements_by_id[s_id] = s
                if utr:
                    store.settlements_by_utr[utr] = s

        # 6. Settlement Recon
        with (p_dir / "settlement_recon.csv").open("r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                e_id = row["entity_id"]
                pay_id = row.get("payment_id", "")
                rec = SettlementReconRecord(
                    entity_id=e_id,
                    type=row.get("type", "payment"),
                    debit_paise=int(row.get("debit", 0)),
                    credit_paise=int(row.get("credit", 0)),
                    amount_paise=int(row.get("amount", 0)),
                    currency=row.get("currency", "INR"),
                    fee_paise=int(row.get("fee", 0)),
                    tax_paise=int(row.get("tax", 0)),
                    on_hold=row.get("on_hold", "false").lower() == "true",
                    settled=row.get("settled", "true").lower() == "true",
                    created_at=int(row.get("created_at", 0)),
                    settled_at=row.get("settled_at", ""),
                    settlement_id=row.get("settlement_id", ""),
                    settlement_utr=row.get("settlement_utr", ""),
                    payment_id=pay_id,
                    order_id=row.get("order_id", ""),
                    method=row.get("method", "upi"),
                    anomaly_type=row.get("anomaly_type", ""),
                )
                store.settlement_recon.append(rec)
                if pay_id:
                    store.recon_by_payment_id[pay_id] = rec

        # 7. Bank Credits
        with (p_dir / "bank_credits.csv").open("r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                bc_id = row["bank_credit_id"]
                s_id = row.get("settlement_id", "")
                utr = row.get("utr", "")
                credit_date = row.get("credit_date", "")
                credit_year = int(credit_date[:4]) if credit_date else int(p_key[:4])

                bc = BankCredit(
                    bank_credit_id=bc_id,
                    settlement_id=s_id,
                    utr=utr,
                    credit_date=credit_date,
                    credit_year=credit_year,
                    amount_paise=int(row["amount"]),
                    currency=row.get("currency", "INR"),
                    bank_status=row.get("bank_status", "credited"),
                    reference=row.get("reference", ""),
                )
                store.bank_credits.append(bc)
                if s_id:
                    store.bank_credits_by_settlement_id[s_id] = bc
                if utr:
                    store.bank_credits_by_utr[utr] = bc

        # 8. Recovery Requests
        with (p_dir / "recovery_requests.csv").open("r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                req_paise = inr_to_paise(row.get("amount_requested", 0))
                rec_paise = inr_to_paise(row.get("amount_recovered", 0))
                req = RecoveryRequest(
                    request_id=row["request_id"],
                    finding_id=row.get("anomaly_id", ""),
                    created_date=row.get("created_date", ""),
                    resolved_date=row.get("resolved_date") if row.get("resolved_date") else None,
                    status=row.get("status", "submitted"),
                    amount_requested_paise=req_paise,
                    amount_recovered_paise=rec_paise,
                    recipient=row.get("recipient", "Razorpay Support"),
                    subject=row.get("subject", ""),
                    summary=row.get("summary", ""),
                    evidence_count=int(row.get("evidence_count", 0)) if str(row.get("evidence_count", "")).isdigit() else 3,
                )
                store.recovery_requests.append(req)

        # 9. Reference Anomalies & Evidence
        with (p_dir / "anomalies.csv").open("r", encoding="utf-8") as f:
            store.reference_anomalies = list(csv.DictReader(f))

        with (p_dir / "anomaly_evidence.csv").open("r", encoding="utf-8") as f:
            store.reference_evidence = list(csv.DictReader(f))

        with (p_dir / "summary.csv").open("r", encoding="utf-8") as f:
            store.monthly_summary = list(csv.DictReader(f))

        self._periods[p_key] = store
        self._loaded_periods.add(p_key)
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "Loaded period %s in %.0f ms (%d payments, %d refunds, %d settlements)",
            p_key,
            elapsed_ms,
            len(store.payments),
            len(store.refunds),
            len(store.settlements),
        )

    def _get_store(self, period: Optional[str] = None, year: Optional[int] = None) -> PeriodStore:
        key = self.ensure_period(period, year)
        return self._periods[key]

    def _iter_period_stores(self):
        seen = set()
        for key, store in list(self._periods.items()):
            seen.add(key)
            yield store
        for key in self.period_keys():
            if key not in seen:
                yield self._get_store(key)

    def _read_merchant_meta(self, p_key: str) -> Tuple[Dict[str, Any], float]:
        p_dir = self.data_dir / p_key
        with (p_dir / "dataset_meta.json").open("r", encoding="utf-8") as f:
            meta = json.load(f)
        fee_rate = 0.018
        fee_file = p_dir / "fee_contracts.csv"
        if fee_file.is_file():
            with fee_file.open("r", encoding="utf-8") as f:
                row = next(csv.DictReader(f), None)
                if row:
                    try:
                        fee_rate = float(row.get("contracted_rate", 0.018))
                    except (ValueError, TypeError):
                        fee_rate = 0.018
        return meta, fee_rate

    # -------------------------------------------------------------------------
    # Getters
    # -------------------------------------------------------------------------

    def get_merchant_data(self, period: Optional[str] = None) -> Dict[str, Any]:
        p_key = self.normalize_period_key(period)
        if p_key in self._periods:
            store = self._periods[p_key]
            meta = store.meta
            fee_rate = store.fee_contracts[0].contracted_rate if store.fee_contracts else 0.018
        else:
            meta, fee_rate = self._read_merchant_meta(p_key)

        dataset_type = meta.get("dataset_type", "synthetic_demo")
        is_synthetic = dataset_type == "synthetic_demo"

        return {
            "merchant_name": meta.get("merchant_name", settings.demo_merchant_name),
            "merchant_id": meta.get("merchant_id", settings.demo_merchant_id),
            "currency": meta.get("currency", "INR"),
            "payment_provider": meta.get("payment_provider", "Razorpay"),
            "dataset_period": {
                "start": meta.get("period_start", "2024-01-01"),
                "end": meta.get("period_end", "2026-12-31"),
                "years": [2024, 2025, 2026],
            },
            "contract": {
                "fee_rate": fee_rate,
                "effective_from": meta.get("period_start", "2024-01-01"),
                "effective_to": meta.get("period_end", "2026-12-31"),
            },
            "demo_status": "Synthetic demo dataset" if is_synthetic else "Connected",
            "dataset_type": dataset_type,
            "finance_email": settings.finance_email,
            "settlement_bank": settings.settlement_bank,
            "initials": "ZC",
            "notes": meta.get("note", "Synthetic data for demonstration purposes only."),
        }

    def get_fee_contract(self, period: Optional[str] = None) -> Optional[FeeContract]:
        store = self._get_store(period)
        return store.fee_contracts[0] if store.fee_contracts else None

    def get_all_payments(self, period: Optional[str] = None, year: Optional[int] = None) -> List[Payment]:
        store = self._get_store(period, year)
        if year is not None:
            return [p for p in store.payments if p.created_year == year]
        return store.payments

    def get_payment_by_id(self, payment_id: str, period: Optional[str] = None) -> Optional[Payment]:
        if period:
            return self._get_store(period).payments_by_id.get(payment_id)
        for store in self._iter_period_stores():
            if payment_id in store.payments_by_id:
                return store.payments_by_id[payment_id]
        return None

    def get_all_refunds(self, period: Optional[str] = None, year: Optional[int] = None) -> List[Refund]:
        store = self._get_store(period, year)
        if year is not None:
            return [r for r in store.refunds if r.created_year == year]
        return store.refunds

    def get_refunds_by_payment_id(self, payment_id: str, period: Optional[str] = None) -> List[Refund]:
        if period:
            return self._get_store(period).refunds_by_payment_id.get(payment_id, [])
        for store in self._iter_period_stores():
            if payment_id in store.refunds_by_payment_id:
                return store.refunds_by_payment_id[payment_id]
        return []

    def get_all_settlements(self, period: Optional[str] = None, year: Optional[int] = None) -> List[Settlement]:
        store = self._get_store(period, year)
        if year is not None:
            return [s for s in store.settlements if s.settlement_year == year]
        return store.settlements

    def get_settlement_by_id(self, settlement_id: str, period: Optional[str] = None) -> Optional[Settlement]:
        if period:
            return self._get_store(period).settlements_by_id.get(settlement_id)
        for store in self._iter_period_stores():
            if settlement_id in store.settlements_by_id:
                return store.settlements_by_id[settlement_id]
        return None

    def get_settlement_by_utr(self, utr: str, period: Optional[str] = None) -> Optional[Settlement]:
        if period:
            return self._get_store(period).settlements_by_utr.get(utr)
        for store in self._iter_period_stores():
            if utr in store.settlements_by_utr:
                return store.settlements_by_utr[utr]
        return None

    def get_all_settlement_recon(self, period: Optional[str] = None) -> List[SettlementReconRecord]:
        store = self._get_store(period)
        return store.settlement_recon

    def get_recon_by_payment_id(self, payment_id: str, period: Optional[str] = None) -> Optional[SettlementReconRecord]:
        if period:
            return self._get_store(period).recon_by_payment_id.get(payment_id)
        for store in self._iter_period_stores():
            if payment_id in store.recon_by_payment_id:
                return store.recon_by_payment_id[payment_id]
        return None

    def get_all_bank_credits(self, period: Optional[str] = None, year: Optional[int] = None) -> List[BankCredit]:
        store = self._get_store(period, year)
        if year is not None:
            return [bc for bc in store.bank_credits if bc.credit_year == year]
        return store.bank_credits

    def get_bank_credit_by_settlement_id(self, settlement_id: str, period: Optional[str] = None) -> Optional[BankCredit]:
        if period:
            return self._get_store(period).bank_credits_by_settlement_id.get(settlement_id)
        for store in self._iter_period_stores():
            if settlement_id in store.bank_credits_by_settlement_id:
                return store.bank_credits_by_settlement_id[settlement_id]
        return None

    def get_bank_credit_by_utr(self, utr: str, period: Optional[str] = None) -> Optional[BankCredit]:
        if period:
            return self._get_store(period).bank_credits_by_utr.get(utr)
        for store in self._iter_period_stores():
            if utr in store.bank_credits_by_utr:
                return store.bank_credits_by_utr[utr]
        return None

    def get_recovery_requests(self, period: Optional[str] = None) -> List[RecoveryRequest]:
        store = self._get_store(period)
        return store.recovery_requests

    def get_reference_anomalies(self, period: Optional[str] = None) -> List[Dict[str, Any]]:
        store = self._get_store(period)
        return store.reference_anomalies

    def get_reference_evidence(self, period: Optional[str] = None) -> List[Dict[str, Any]]:
        store = self._get_store(period)
        return store.reference_evidence

    def get_monthly_summary_records(self, period: Optional[str] = None, year: Optional[int] = None) -> List[Dict[str, Any]]:
        store = self._get_store(period, year)
        return store.monthly_summary


# Singleton repository instance
data_repository = DataRepository()
