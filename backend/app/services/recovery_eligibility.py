"""
Anomaly-level recovery eligibility.

These rules are evidence-based. They do not apply a global 80/85/90% haircut.

Money Affected  = verified financial impact from source records.
Potential Recovery = sum of recoverable_amount_paise on eligible confirmed findings.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RecoveryDecision:
    is_eligible: bool
    recoverable_paise: int
    reason: str


def fee_overcharge(
    excess_fee_paise: int,
    excess_tax_paise: int = 0,
) -> RecoveryDecision:
    """
    Contracted MDR was breached. The entire excess fee is a Razorpay billing error
    and is recoverable in full.

    GST collected on the excess MDR (tax_paise) is remitted to GSTN. It is money
    affected but is recovered via GST credit, not a Razorpay dispute.
    """
    excess_fee_paise = max(0, int(excess_fee_paise))
    excess_tax_paise = max(0, int(excess_tax_paise))
    if excess_tax_paise > 0:
        return RecoveryDecision(
            is_eligible=True,
            recoverable_paise=excess_fee_paise,
            reason="Excess GST on MDR is remitted to GSTN and is not recovered via a Razorpay dispute.",
        )
    return RecoveryDecision(
        is_eligible=True,
        recoverable_paise=excess_fee_paise,
        reason="Full excess MDR is a contracted-rate billing error and is recoverable from Razorpay.",
    )


def duplicate_refund(excess_paise: int) -> RecoveryDecision:
    """Duplicate customer refund debit is fully reversible with acquirer trace."""
    return RecoveryDecision(
        is_eligible=True,
        recoverable_paise=max(0, int(excess_paise)),
        reason="Duplicate refund debit is fully reversible against the original payment trace.",
    )


def missing_settlement(
    captured_gross_paise: int,
    contracted_rate: float,
    tax_paise: int = 0,
) -> RecoveryDecision:
    """
    Money Affected is the captured gross (the payment never settled).

    Razorpay would have credited NET of contracted MDR and tax. Only that net
    amount is recoverable as a missing settlement.
    """
    captured_gross_paise = max(0, int(captured_gross_paise))
    contracted_fee_paise = int(round(captured_gross_paise * float(contracted_rate)))
    tax_paise = max(0, int(tax_paise))
    recoverable = max(0, captured_gross_paise - contracted_fee_paise - tax_paise)
    return RecoveryDecision(
        is_eligible=recoverable > 0,
        recoverable_paise=recoverable,
        reason="Missing settlement recovery is the net amount that would have been credited after contracted MDR.",
    )


def bank_credit_missing(
    missing_credit_paise: int,
    is_ifsc_or_account_return: bool,
) -> RecoveryDecision:
    """
    IFSC / account-detail returns are a merchant bank-detail issue, not a Razorpay
    payout error, so they are not gateway-dispute recoverable.

    An unexplained processed settlement with no bank UTR credit is fully recoverable
    from Razorpay (the funds never left the nodal account).
    """
    missing_credit_paise = max(0, int(missing_credit_paise))
    if is_ifsc_or_account_return:
        return RecoveryDecision(
            is_eligible=False,
            recoverable_paise=0,
            reason="Bank returned the credit due to IFSC/account-detail mismatch; not recoverable via Razorpay dispute.",
        )
    return RecoveryDecision(
        is_eligible=True,
        recoverable_paise=missing_credit_paise,
        reason="Processed Razorpay settlement has no matching bank UTR credit; full missing credit is recoverable.",
    )


def settlement_amount_discrepancy(
    shortfall_paise: int,
    is_explained_holdback: bool,
) -> RecoveryDecision:
    """
    Unexplained payout shortfall is recoverable in full.

    A shortfall that reconcilers (or the gateway) have already explained as a
    legitimate merchant chargeback/holdback is money affected but not recoverable.
    """
    shortfall_paise = max(0, int(shortfall_paise))
    if is_explained_holdback:
        return RecoveryDecision(
            is_eligible=False,
            recoverable_paise=0,
            reason="Shortfall is explained as a merchant chargeback/holdback, not a gateway payout error.",
        )
    return RecoveryDecision(
        is_eligible=True,
        recoverable_paise=shortfall_paise,
        reason="Unexplained settlement shortfall versus calculated net payout is recoverable in full.",
    )


def uncredited_refund(refund_paise: int) -> RecoveryDecision:
    """Merchant was debited; customer was not credited. Full reversal is due."""
    return RecoveryDecision(
        is_eligible=True,
        recoverable_paise=max(0, int(refund_paise)),
        reason="Refund was debited from the merchant and never credited to the customer; full amount is recoverable.",
    )


def settlement_delay() -> RecoveryDecision:
    """Temporary SLA breach. Funds arrived; this is not permanent lost money."""
    return RecoveryDecision(
        is_eligible=False,
        recoverable_paise=0,
        reason="Settlement delay is an SLA breach with no permanent monetary loss once the credit arrives.",
    )


def from_reference_row(row: Optional[dict], computed_impact_paise: int) -> RecoveryDecision:
    """
    Apply documented eligibility from the reference anomaly row.
    Impact remains the computed source-record amount; eligibility is not a percentage.
    """
    if not row:
        return RecoveryDecision(True, max(0, computed_impact_paise), "")
    raw = str(row.get("is_recovery_eligible", "true")).strip().lower()
    eligible = raw in ("true", "1", "yes")
    reason = str(row.get("recovery_ineligibility_reason", "") or "")
    if not eligible:
        return RecoveryDecision(False, 0, reason)
    return RecoveryDecision(True, max(0, computed_impact_paise), reason)
