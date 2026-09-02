from typing import List, Optional

from app.models.domain import EvidenceItem, Finding
from app.services.data_repository import DataRepository
from app.services.detectors.finding_ids import finding_id_for, is_explained_holdback
from app.services import recovery_eligibility as eligibility

# Ignore sub-rupee rounding; injected demo shortfalls are thousands of rupees.
SHORTFALL_THRESHOLD_PAISE = 100


class SettlementDiscrepancyDetector:
    """
    Compares calculated net settlement (payments - fees - refund adjustments)
    against the actual settlement payout recorded on the source settlement.

    Money Affected = expected net - actual payout.
    Recovery eligibility is full shortfall unless the reference row documents
    a legitimate chargeback/holdback explanation.
    """

    def __init__(self, repo: DataRepository):
        self.repo = repo

    def detect(self, period: Optional[str] = None, year: Optional[int] = None) -> List[Finding]:
        p_key = self.repo.normalize_period_key(period, year)
        settlements = self.repo.get_all_settlements(period=p_key, year=year)
        recon = self.repo.get_all_settlement_recon(period=p_key)
        if not settlements:
            return []

        recon_by_settlement = {}
        for rec in recon:
            if rec.type != "payment" or not rec.settlement_id:
                continue
            recon_by_settlement.setdefault(rec.settlement_id, []).append(rec)

        findings: List[Finding] = []
        for s in settlements:
            batch = recon_by_settlement.get(s.id, [])
            if batch:
                expected_paise = (
                    sum(r.amount_paise - r.fee_paise for r in batch) - s.refund_adjustment_paise
                )
            else:
                expected_paise = s.amount_paise + s.refund_adjustment_paise
            expected_paise = max(0, expected_paise)
            shortfall_paise = expected_paise - s.amount_paise
            if shortfall_paise <= SHORTFALL_THRESHOLD_PAISE:
                continue

            finding_id, ref = finding_id_for(
                self.repo, p_key, "settlement_amount_discrepancy", f"anom_{p_key}_sd_{s.id}", s.id
            )
            holdback = is_explained_holdback(ref)
            decision = eligibility.settlement_amount_discrepancy(shortfall_paise, holdback)

            ev = EvidenceItem(
                evidence_id=f"ev_settl_disc_{p_key}_{s.id}",
                source_record_id=s.id,
                reference_id=s.utr,
                date=s.settlement_date,
                method="NEFT/RTGS",
                gross_amount_paise=expected_paise,
                expected_value=f"INR {expected_paise / 100:,.2f}",
                actual_value=f"INR {s.amount_inr:,.2f}",
                difference=f"INR {shortfall_paise / 100:,.2f}",
                financial_impact_paise=shortfall_paise,
                evidence_note="Calculated net payout versus actual settlement amount.",
            )

            findings.append(
                Finding(
                    finding_id=finding_id,
                    type="settlement_amount_discrepancy",
                    status="confirmed",
                    title="Settlement Amount Discrepancy",
                    description=(
                        f"Settlement {s.id} payout was short by INR {shortfall_paise / 100:,.2f} "
                        f"versus calculated net batch total."
                    ),
                    simple_explanation="Net bank deposit received was short compared to gross minus legitimate fees.",
                    financial_impact_paise=shortfall_paise,
                    currency="INR",
                    affected_transaction_count=s.payment_count if s.payment_count > 0 else len(batch) or 1,
                    detected_at=s.settlement_date,
                    start_date=s.settlement_date,
                    end_date=s.settlement_date,
                    confidence=1.0,
                    root_cause_reference=(
                        (ref or {}).get("root_cause")
                        or f"Settlement {s.id} was short versus calculated net payout."
                    ),
                    source_record_ids=[s.id] + [r.payment_id for r in batch[:8] if r.payment_id],
                    evidence=[ev],
                    verification_method_a=f"Calculated net batch settlement = INR {expected_paise / 100:,.2f}",
                    verification_method_b=(
                        f"Actual settlement payout = INR {s.amount_inr:,.2f} "
                        f"(Shortfall: INR {shortfall_paise / 100:,.2f})"
                    ),
                    is_verified=True,
                    is_recovery_eligible=decision.is_eligible,
                    recoverable_amount_paise=decision.recoverable_paise,
                    recovery_ineligibility_reason=decision.reason if not decision.is_eligible else "",
                )
            )
        return findings
