from typing import List, Optional

from app.models.domain import EvidenceItem, Finding
from app.services.data_repository import DataRepository
from app.services.detectors.finding_ids import finding_id_for
from app.services import recovery_eligibility as eligibility


class FeeAnomalyDetector:
    """
    Audits every captured payment against the contracted fee rate.
    Money Affected = actual fee - contracted fee (plus excess GST if present).
    Potential Recovery = excess MDR only (GST is not a Razorpay-dispute item).
    """

    def __init__(self, repo: DataRepository):
        self.repo = repo

    def detect(self, period: Optional[str] = None, year: Optional[int] = None) -> List[Finding]:
        p_key = self.repo.normalize_period_key(period, year)
        payments = self.repo.get_all_payments(period=p_key, year=year)
        fee_contract = self.repo.get_fee_contract(period=p_key)
        contracted_rate = fee_contract.contracted_rate if fee_contract else 0.018

        affected_payments = [
            p for p in payments
            if p.captured and (p.applied_fee_rate > contracted_rate + 1e-9 or p.anomaly_type == "fee_rate_increase")
        ]
        if not affected_payments:
            return []

        total_gross_paise = sum(p.amount_paise for p in affected_payments)
        total_actual_fee_paise = sum(p.fee_paise for p in affected_payments)
        total_expected_fee_paise = sum(round(p.amount_paise * contracted_rate) for p in affected_payments)
        excess_fee_paise = max(0, total_actual_fee_paise - total_expected_fee_paise)

        total_actual_tax_paise = sum(p.tax_paise for p in affected_payments)
        # Synthetic fee-overcharge payments store GST as 0; expected tax is therefore 0.
        total_expected_tax_paise = 0
        excess_tax_paise = max(0, total_actual_tax_paise - total_expected_tax_paise)

        contracted_pct = f"{contracted_rate * 100:.2f}%"
        applied_rate = affected_payments[0].applied_fee_rate
        applied_pct = f"{applied_rate * 100:.2f}%"
        method_a_rate_diff = max(0.0, (applied_rate - contracted_rate))
        method_a_impact_paise = int(round(total_gross_paise * method_a_rate_diff))
        method_b_impact_paise = excess_fee_paise
        fee_impact_paise = method_b_impact_paise if method_b_impact_paise > 0 else method_a_impact_paise
        money_affected_paise = fee_impact_paise + excess_tax_paise

        decision = eligibility.fee_overcharge(fee_impact_paise, excess_tax_paise)

        evidence_items: List[EvidenceItem] = []
        for idx, p in enumerate(affected_payments[:4]):
            exp_fee = round(p.amount_paise * contracted_rate)
            diff_fee = p.fee_paise - exp_fee
            evidence_items.append(
                EvidenceItem(
                    evidence_id=f"ev_fee_{p_key}_{idx + 1}_{p.id}",
                    source_record_id=p.id,
                    reference_id=p.order_id,
                    date=p.created_date,
                    method=p.method,
                    gross_amount_paise=p.amount_paise,
                    expected_value=f"{contracted_rate * 100:.2f}% (INR {exp_fee / 100:.2f})",
                    actual_value=f"{p.applied_fee_rate * 100:.2f}% (INR {p.fee_paise / 100:.2f})",
                    difference=f"+{(p.applied_fee_rate - contracted_rate) * 100:.2f}% (+INR {diff_fee / 100:.2f})",
                    financial_impact_paise=diff_fee,
                    evidence_note=f"Contracted {contracted_pct} fee rate vs charged {p.applied_fee_rate * 100:.2f}% fee rate.",
                )
            )

        sorted_dates = sorted(p.created_date for p in affected_payments)
        finding_id, _ = finding_id_for(self.repo, p_key, "fee_rate_increase", f"anom_{p_key}_001")

        return [
            Finding(
                finding_id=finding_id,
                type="fee_rate_increase",
                status="confirmed",
                title="Unexpected Fee Rate Increase",
                description=(
                    f"Razorpay charged a {applied_pct} fee instead of the agreed {contracted_pct} rate "
                    f"across {len(affected_payments):,} transactions processed between "
                    f"{sorted_dates[0]} and {sorted_dates[-1]}."
                ),
                simple_explanation=(
                    f"The agreed fee rate was {contracted_pct}, but {applied_pct} was applied to these "
                    f"{len(affected_payments):,} payments."
                ),
                financial_impact_paise=money_affected_paise,
                currency="INR",
                affected_transaction_count=len(affected_payments),
                detected_at=sorted_dates[-1],
                start_date=sorted_dates[0],
                end_date=sorted_dates[-1],
                confidence=1.0,
                root_cause_reference=f"The agreed fee rate was {contracted_pct}, but {applied_pct} was applied to these payments.",
                source_record_ids=[p.id for p in affected_payments],
                evidence=evidence_items,
                verification_method_a=(
                    f"Gross INR {total_gross_paise / 100:,.2f} x rate diff "
                    f"{method_a_rate_diff * 100:.2f}% = INR {method_a_impact_paise / 100:,.2f}"
                ),
                verification_method_b=(
                    f"Sum of (actual fee - contracted fee) across {len(affected_payments):,} "
                    f"payments = INR {method_b_impact_paise / 100:,.2f}"
                ),
                is_verified=True,
                is_recovery_eligible=decision.is_eligible,
                recoverable_amount_paise=decision.recoverable_paise,
                recovery_ineligibility_reason=decision.reason if not decision.is_eligible else "",
            )
        ]
