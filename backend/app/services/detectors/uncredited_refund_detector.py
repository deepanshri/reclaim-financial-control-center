from typing import List, Optional

from app.models.domain import EvidenceItem, Finding
from app.services.data_repository import DataRepository
from app.services.detectors.finding_ids import finding_id_for
from app.services import recovery_eligibility as eligibility


class UncreditedRefundDetector:
    """
    Refunds debited from the merchant that have no acquirer UTR / customer credit.
    Money Affected = refund amount. Potential Recovery = full refund amount.
    """

    def __init__(self, repo: DataRepository):
        self.repo = repo

    def detect(self, period: Optional[str] = None, year: Optional[int] = None) -> List[Finding]:
        p_key = self.repo.normalize_period_key(period, year)
        refunds = self.repo.get_all_refunds(period=p_key, year=year)
        tagged = [r for r in refunds if r.anomaly_type == "uncredited_refund"]
        untagged_empty_utr = [
            r for r in refunds
            if r.anomaly_type != "uncredited_refund" and not (r.acquirer_utr or "").strip()
        ]

        findings: List[Finding] = []
        for r in tagged:
            payment = self.repo.get_payment_by_id(r.payment_id, period=p_key)
            decision = eligibility.uncredited_refund(r.amount_paise)
            finding_id, _ = finding_id_for(
                self.repo, p_key, "uncredited_refund", f"anom_{p_key}_uc_{r.id}", r.id
            )
            ev = EvidenceItem(
                evidence_id=f"ev_uncred_rf_{p_key}_{r.id}",
                source_record_id=r.id,
                reference_id=r.payment_id,
                date=r.created_date,
                method=payment.method if payment else "upi",
                gross_amount_paise=r.amount_paise,
                expected_value=f"INR {r.amount_inr:,.2f} credited to customer",
                actual_value="INR 0.00 (no acquirer UTR)",
                difference=f"INR {r.amount_inr:,.2f}",
                financial_impact_paise=r.amount_paise,
                evidence_note="Refund debited from merchant; customer bank credit not confirmed.",
            )
            findings.append(
                Finding(
                    finding_id=finding_id,
                    type="uncredited_refund",
                    status="confirmed",
                    title="Refund Not Received by Customer",
                    description=(
                        f"Refund {r.id} of INR {r.amount_inr:,.2f} was initiated for payment "
                        f"{r.payment_id} but the customer bank account did not receive credit."
                    ),
                    simple_explanation="A customer refund was deducted from your account but never reached the customer.",
                    financial_impact_paise=r.amount_paise,
                    currency="INR",
                    affected_transaction_count=1,
                    detected_at=r.created_date,
                    start_date=r.created_date,
                    end_date=r.created_date,
                    confidence=1.0,
                    root_cause_reference="Refund debited from merchant; acquirer UTR not confirmed.",
                    source_record_ids=[r.id, r.payment_id],
                    evidence=[ev],
                    verification_method_a=f"Refund amount = INR {r.amount_inr:,.2f} debited from merchant account",
                    verification_method_b="Customer bank UTR confirmation = not received",
                    is_verified=True,
                    is_recovery_eligible=decision.is_eligible,
                    recoverable_amount_paise=decision.recoverable_paise,
                    recovery_ineligibility_reason="",
                )
            )
        if untagged_empty_utr:
            sample = untagged_empty_utr[0]
            total_paise = sum(r.amount_paise for r in untagged_empty_utr)
            findings.append(
                Finding(
                    finding_id=f"anom_{p_key}_uncredited_refund_review",
                    type="uncredited_refund",
                    status="under_review",
                    title="Refunds missing an acquirer UTR",
                    description=(
                        f"{len(untagged_empty_utr)} refunds totalling INR {total_paise / 100:,.2f} "
                        "have no acquirer UTR on file and are held for review."
                    ),
                    simple_explanation="Some refunds do not yet have a customer-credit UTR. They are under review, not confirmed loss.",
                    financial_impact_paise=total_paise,
                    currency="INR",
                    affected_transaction_count=len(untagged_empty_utr),
                    detected_at=sample.created_date,
                    start_date=min(r.created_date for r in untagged_empty_utr),
                    end_date=max(r.created_date for r in untagged_empty_utr),
                    confidence=0.6,
                    root_cause_reference="Refund without acquirer UTR.",
                    source_record_ids=[r.id for r in untagged_empty_utr[:25]],
                    evidence=[],
                    verification_method_a=f"Refunds with empty acquirer UTR = {len(untagged_empty_utr)}",
                    verification_method_b="Not booked as confirmed until customer credit can be disproved.",
                    is_verified=False,
                    is_recovery_eligible=False,
                    recoverable_amount_paise=0,
                    recovery_ineligibility_reason="Held for review pending acquirer UTR confirmation.",
                )
            )
        return findings
