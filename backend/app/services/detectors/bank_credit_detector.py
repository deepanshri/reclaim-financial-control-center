from typing import List, Optional

from app.models.domain import EvidenceItem, Finding
from app.services.data_repository import DataRepository
from app.services.detectors.finding_ids import finding_id_for, is_ifsc_return
from app.services import recovery_eligibility as eligibility


class BankCreditDetector:
    """
    Processed Razorpay settlements with no matching bank credit for their UTR.

    Confirmed findings are tagged gaps or modest dedicated anomaly payouts.
    Large untagged daily batches without a bank UTR are raised as a single
    under-review finding instead of being silently ignored.
    """

    def __init__(self, repo: DataRepository):
        self.repo = repo

    def detect(self, period: Optional[str] = None, year: Optional[int] = None) -> List[Finding]:
        p_key = self.repo.normalize_period_key(period, year)
        settlements = self.repo.get_all_settlements(period=p_key, year=year)
        if not settlements:
            return []

        findings: List[Finding] = []
        review_batch = []
        for s in settlements:
            if s.status != "processed":
                continue
            matching_bc = self.repo.get_bank_credit_by_settlement_id(s.id, period=p_key)
            if not matching_bc:
                matching_bc = self.repo.get_bank_credit_by_utr(s.utr, period=p_key)
            if matching_bc:
                continue

            tagged = (getattr(s, "anomaly_type", "") or "") == "bank_credit_missing"
            if not tagged and s.amount_paise > 10_000_000:
                review_batch.append(s)
                continue

            impact_paise = s.amount_paise
            finding_id, ref = finding_id_for(
                self.repo, p_key, "bank_credit_missing", f"anom_{p_key}_004", s.id
            )
            ifsc = is_ifsc_return(ref, title=str((ref or {}).get("title", "")), reason="")
            decision = eligibility.bank_credit_missing(impact_paise, is_ifsc_or_account_return=ifsc)

            title = (ref or {}).get("title") or (
                "Settlement Returned — Bank IFSC Update" if ifsc else "Settlement Not Found in Bank"
            )
            root_cause = (ref or {}).get("root_cause") or (
                f"Settlement {s.id} with UTR {s.utr} has no corresponding bank credit record."
            )

            ev = EvidenceItem(
                evidence_id=f"ev_bank_miss_{p_key}_{s.id}",
                source_record_id=s.id,
                reference_id=s.utr,
                date=s.settlement_date,
                method="Bank Settlement",
                gross_amount_paise=s.amount_paise,
                expected_value=f"Bank Credit of INR {s.amount_inr:,.2f} (UTR {s.utr})",
                actual_value="No credit in bank account (INR 0.00)",
                difference=f"Missing deposit of INR {s.amount_inr:,.2f}",
                financial_impact_paise=impact_paise,
                evidence_note="A processed Razorpay settlement has no matching bank credit for its UTR.",
            )

            findings.append(
                Finding(
                    finding_id=finding_id,
                    type="bank_credit_missing",
                    status="confirmed",
                    title=title,
                    description=(
                        f"Razorpay settlement {s.id} (UTR {s.utr}) of INR {s.amount_inr:,.2f} "
                        f"on {s.settlement_date} is marked processed but was never credited "
                        f"to the merchant bank account."
                    ),
                    simple_explanation=root_cause,
                    financial_impact_paise=impact_paise,
                    currency="INR",
                    affected_transaction_count=s.payment_count if s.payment_count > 0 else 1,
                    detected_at=s.settlement_date,
                    start_date=s.settlement_date,
                    end_date=s.settlement_date,
                    confidence=1.0,
                    root_cause_reference=root_cause,
                    source_record_ids=[s.id, s.utr],
                    evidence=[ev],
                    verification_method_a=f"Settlement amount from Razorpay ledger = INR {s.amount_inr:,.2f}",
                    verification_method_b=f"Bank credit search for UTR {s.utr} = 0 records found",
                    is_verified=True,
                    is_recovery_eligible=decision.is_eligible,
                    recoverable_amount_paise=decision.recoverable_paise,
                    recovery_ineligibility_reason=decision.reason if not decision.is_eligible else "",
                )
            )

        if review_batch:
            total_paise = sum(s.amount_paise for s in review_batch)
            sample = review_batch[0]
            findings.append(
                Finding(
                    finding_id=f"anom_{p_key}_bank_credit_review",
                    type="bank_credit_missing",
                    status="under_review",
                    title="Large settlements awaiting bank UTR match",
                    description=(
                        f"{len(review_batch)} processed settlements totalling INR {total_paise / 100:,.2f} "
                        "have no matching bank credit yet. They are held for review rather than booked as confirmed loss."
                    ),
                    simple_explanation="Large processed payouts are missing a bank UTR credit and need review before they are treated as confirmed loss.",
                    financial_impact_paise=total_paise,
                    currency="INR",
                    affected_transaction_count=len(review_batch),
                    detected_at=sample.settlement_date,
                    start_date=min(s.settlement_date for s in review_batch),
                    end_date=max(s.settlement_date for s in review_batch),
                    confidence=0.6,
                    root_cause_reference="Processed settlement with no bank credit; batch size requires manual confirmation.",
                    source_record_ids=[s.id for s in review_batch[:25]],
                    evidence=[
                        EvidenceItem(
                            evidence_id=f"ev_bank_review_{p_key}_{sample.id}",
                            source_record_id=sample.id,
                            reference_id=sample.utr,
                            date=sample.settlement_date,
                            method="Bank Settlement",
                            gross_amount_paise=sample.amount_paise,
                            expected_value="Matching bank UTR credit",
                            actual_value="Not matched yet",
                            difference=f"{len(review_batch)} settlements",
                            financial_impact_paise=total_paise,
                            evidence_note="Aggregated untagged large settlements without a bank credit row.",
                        )
                    ],
                    verification_method_a=f"Count of unmatched processed settlements = {len(review_batch)}",
                    verification_method_b=f"Sum of unmatched settlement amounts = INR {total_paise / 100:,.2f}",
                    is_verified=False,
                    is_recovery_eligible=False,
                    recoverable_amount_paise=0,
                    recovery_ineligibility_reason="Held for review until UTR matching is confirmed.",
                )
            )
        return findings
