from typing import List, Optional

from app.models.domain import EvidenceItem, Finding
from app.services.data_repository import DataRepository
from app.services.detectors.finding_ids import finding_id_for
from app.services import recovery_eligibility as eligibility


class DuplicateRefundDetector:
    """
    Groups refunds by payment ID and flags duplicate executions.
    Money Affected = excess debit above the original legitimate refund.
    Potential Recovery = the full excess (duplicate debit is fully reversible).
    """

    def __init__(self, repo: DataRepository):
        self.repo = repo

    def detect(self, period: Optional[str] = None, year: Optional[int] = None) -> List[Finding]:
        p_key = self.repo.normalize_period_key(period, year)
        refunds = self.repo.get_all_refunds(period=p_key, year=year)
        if not refunds:
            return []

        duplicate_refunds = [
            r for r in refunds
            if r.duplicate_of_refund_id or r.anomaly_type == "duplicate_refund"
        ]
        if not duplicate_refunds:
            return []

        findings: List[Finding] = []
        for idx, dup in enumerate(duplicate_refunds):
            parent_payment_id = dup.payment_id
            all_payment_refunds = self.repo.get_refunds_by_payment_id(parent_payment_id, period=p_key)
            parent_payment = self.repo.get_payment_by_id(parent_payment_id, period=p_key)

            original_refund = next(
                (r for r in all_payment_refunds if r.id == dup.duplicate_of_refund_id),
                all_payment_refunds[0] if all_payment_refunds else None,
            )

            total_refunded_paise = sum(r.amount_paise for r in all_payment_refunds)
            expected_refund_paise = original_refund.amount_paise if original_refund else dup.amount_paise
            method_a_excess_paise = max(0, total_refunded_paise - expected_refund_paise)
            method_b_excess_paise = dup.amount_paise
            impact_paise = method_a_excess_paise if method_a_excess_paise > 0 else method_b_excess_paise
            decision = eligibility.duplicate_refund(impact_paise)

            evidence_items: List[EvidenceItem] = []
            if original_refund:
                evidence_items.append(
                    EvidenceItem(
                        evidence_id=f"ev_ref_{p_key}_{idx + 1:03d}_orig",
                        source_record_id=original_refund.id,
                        reference_id=parent_payment_id,
                        date=original_refund.created_date,
                        method=parent_payment.method if parent_payment else "upi",
                        gross_amount_paise=original_refund.amount_paise,
                        expected_value=f"INR {original_refund.amount_inr:,.2f}",
                        actual_value=f"INR {original_refund.amount_inr:,.2f}",
                        difference="INR 0.00",
                        financial_impact_paise=0,
                        evidence_note="Original legitimate refund processed for payment.",
                    )
                )
            evidence_items.append(
                EvidenceItem(
                    evidence_id=f"ev_ref_{p_key}_{idx + 1:03d}_dup",
                    source_record_id=dup.id,
                    reference_id=parent_payment_id,
                    date=dup.created_date,
                    method=parent_payment.method if parent_payment else "upi",
                    gross_amount_paise=dup.amount_paise,
                    expected_value="INR 0.00 (Already refunded)",
                    actual_value=f"INR {dup.amount_inr:,.2f}",
                    difference=f"+INR {dup.amount_inr:,.2f}",
                    financial_impact_paise=dup.amount_paise,
                    evidence_note="Second refund processed for the same payment; excess debit.",
                )
            )

            start_date = original_refund.created_date if original_refund else dup.created_date
            finding_id, _ = finding_id_for(
                self.repo, p_key, "duplicate_refund", f"anom_{p_key}_002", dup.id
            )

            findings.append(
                Finding(
                    finding_id=finding_id,
                    type="duplicate_refund",
                    status="confirmed",
                    title="Duplicate Refund",
                    description=(
                        f"A refund of INR {dup.amount_inr:,.2f} was debited twice against payment "
                        f"{parent_payment_id}. The second refund created an excess debit of "
                        f"INR {dup.amount_inr:,.2f}."
                    ),
                    simple_explanation="The same refund was processed twice for one payment.",
                    financial_impact_paise=impact_paise,
                    currency="INR",
                    affected_transaction_count=1,
                    detected_at=dup.created_date,
                    start_date=start_date,
                    end_date=dup.created_date,
                    confidence=1.0,
                    root_cause_reference="The same refund was processed twice for one payment.",
                    source_record_ids=[r.id for r in all_payment_refunds]
                    + ([parent_payment_id] if parent_payment_id else []),
                    evidence=evidence_items,
                    verification_method_a=(
                        f"Total refunded (INR {total_refunded_paise / 100:,.2f}) - Expected "
                        f"(INR {expected_refund_paise / 100:,.2f}) = INR {method_a_excess_paise / 100:,.2f}"
                    ),
                    verification_method_b=(
                        f"Duplicate refund transaction ({dup.id}) amount = "
                        f"INR {method_b_excess_paise / 100:,.2f}"
                    ),
                    is_verified=True,
                    is_recovery_eligible=decision.is_eligible,
                    recoverable_amount_paise=decision.recoverable_paise,
                    recovery_ineligibility_reason="",
                )
            )

        return findings
