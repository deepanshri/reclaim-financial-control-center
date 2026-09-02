from typing import List, Optional

from app.models.domain import EvidenceItem, Finding
from app.services.data_repository import DataRepository
from app.services.detectors.finding_ids import finding_id_for
from app.services import recovery_eligibility as eligibility


class MissingSettlementDetector:
    """
    Captured payments with no processed settlement.
    Money Affected = captured gross.
    Potential Recovery = net settlement (gross - contracted MDR - tax).
    """

    def __init__(self, repo: DataRepository):
        self.repo = repo

    def detect(self, period: Optional[str] = None, year: Optional[int] = None) -> List[Finding]:
        p_key = self.repo.normalize_period_key(period, year)
        fee_contract = self.repo.get_fee_contract(period=p_key)
        contracted_rate = fee_contract.contracted_rate if fee_contract else 0.018

        recon_records = self.repo.get_all_settlement_recon(period=p_key)
        unsettled_recon = [
            r for r in recon_records
            if r.type == "payment" and (r.anomaly_type == "missing_settlement" or not r.settled)
        ]

        missing_payments = []
        seen = set()
        review_payments = []
        for rec in unsettled_recon:
            parent = self.repo.get_payment_by_id(rec.payment_id, period=p_key)
            if not parent or parent.id in seen:
                continue
            seen.add(parent.id)
            if rec.anomaly_type == "missing_settlement" or parent.anomaly_type == "missing_settlement":
                missing_payments.append(parent)
            else:
                review_payments.append(parent)

        if not missing_payments:
            payments = self.repo.get_all_payments(period=p_key, year=year)
            missing_payments = [p for p in payments if p.captured and p.anomaly_type == "missing_settlement"]

        findings: List[Finding] = []
        for p in missing_payments:
            impact_paise = p.amount_paise
            decision = eligibility.missing_settlement(p.amount_paise, contracted_rate, p.tax_paise)
            finding_id, _ = finding_id_for(
                self.repo, p_key, "missing_settlement", f"anom_{p_key}_003", p.id
            )
            ev = EvidenceItem(
                evidence_id=f"ev_miss_settl_{p_key}_{p.id}",
                source_record_id=p.id,
                reference_id=p.order_id,
                date=p.created_date,
                method=p.method,
                gross_amount_paise=p.amount_paise,
                expected_value=f"INR {p.amount_inr:,.2f}",
                actual_value="INR 0.00",
                difference=f"INR {p.amount_inr:,.2f}",
                financial_impact_paise=impact_paise,
                evidence_note="The payment was captured but no matching processed settlement was found.",
            )
            findings.append(
                Finding(
                    finding_id=finding_id,
                    type="missing_settlement",
                    status="confirmed",
                    title="Payment Not Settled",
                    description=(
                        f"Payment {p.id} of INR {p.amount_inr:,.2f} was captured on {p.created_date} "
                        "but has no corresponding bank settlement record."
                    ),
                    simple_explanation="The payment was captured but no matching processed settlement was found.",
                    financial_impact_paise=impact_paise,
                    currency="INR",
                    affected_transaction_count=1,
                    detected_at=p.created_date,
                    start_date=p.created_date,
                    end_date=p.created_date,
                    confidence=1.0,
                    root_cause_reference="The payment was captured but no matching processed settlement was found.",
                    source_record_ids=[p.id],
                    evidence=[ev],
                    verification_method_a=f"Captured payment amount = INR {p.amount_inr:,.2f}",
                    verification_method_b="Settlement reconciliation status = unsettled",
                    is_verified=True,
                    is_recovery_eligible=decision.is_eligible,
                    recoverable_amount_paise=decision.recoverable_paise,
                    recovery_ineligibility_reason=decision.reason if decision.recoverable_paise != impact_paise else "",
                )
            )

        if review_payments:
            sample = review_payments[0]
            total_paise = sum(p.amount_paise for p in review_payments)
            findings.append(
                Finding(
                    finding_id=f"anom_{p_key}_missing_settlement_review",
                    type="missing_settlement",
                    status="under_review",
                    title="Captured payments not yet in a processed settlement",
                    description=(
                        f"{len(review_payments)} captured payments totalling INR {total_paise / 100:,.2f} "
                        "are not in a processed settlement batch and are held for review."
                    ),
                    simple_explanation="Some captured payments are not in a processed settlement yet. They are under review, not booked as confirmed loss.",
                    financial_impact_paise=total_paise,
                    currency="INR",
                    affected_transaction_count=len(review_payments),
                    detected_at=sample.created_date,
                    start_date=min(p.created_date for p in review_payments),
                    end_date=max(p.created_date for p in review_payments),
                    confidence=0.6,
                    root_cause_reference="Captured payment with no processed settlement in recon.",
                    source_record_ids=[p.id for p in review_payments[:25]],
                    evidence=[],
                    verification_method_a=f"Untagged unsettled recon rows = {len(review_payments)}",
                    verification_method_b="Not included in confirmed money affected until settlement SLA is exceeded.",
                    is_verified=False,
                    is_recovery_eligible=False,
                    recoverable_amount_paise=0,
                    recovery_ineligibility_reason="Held for review; settlement may still be in the T+1 window.",
                )
            )
        return findings
