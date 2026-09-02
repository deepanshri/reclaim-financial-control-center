from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class Payment:
    id: str
    amount_paise: int
    currency: str
    status: str
    order_id: str
    invoice_id: str
    description: str
    method: str
    international: bool
    refund_status: Optional[str]
    amount_refunded_paise: int
    captured: bool
    email: str
    contact: str
    fee_paise: int
    tax_paise: int
    created_at: int
    created_at_dt: str
    created_date: str
    created_year: int
    contract_fee_rate: float
    applied_fee_rate: float
    base_fee_inr: float
    anomaly_type: str = ""

    @property
    def amount_inr(self) -> float:
        return round(self.amount_paise / 100.0, 2)

    @property
    def fee_inr(self) -> float:
        return round(self.fee_paise / 100.0, 2)


@dataclass
class Refund:
    id: str
    payment_id: str
    amount_paise: int
    currency: str
    created_at: int
    created_at_dt: str
    created_date: str
    created_year: int
    receipt: str
    status: str
    speed_requested: str
    speed_processed: str
    acquirer_utr: str
    anomaly_type: str = ""
    duplicate_of_refund_id: str = ""

    @property
    def amount_inr(self) -> float:
        return round(self.amount_paise / 100.0, 2)


@dataclass
class Settlement:
    id: str
    amount_paise: int
    status: str
    fees_paise: int
    tax_paise: int
    utr: str
    created_at: int
    settlement_date: str
    settlement_year: int
    payment_count: int
    refund_adjustment_paise: int
    anomaly_type: str = ""

    @property
    def amount_inr(self) -> float:
        return round(self.amount_paise / 100.0, 2)

    @property
    def fees_inr(self) -> float:
        return round(self.fees_paise / 100.0, 2)


@dataclass
class SettlementReconRecord:
    entity_id: str
    type: str
    debit_paise: int
    credit_paise: int
    amount_paise: int
    currency: str
    fee_paise: int
    tax_paise: int
    on_hold: bool
    settled: bool
    created_at: int
    settled_at: str
    settlement_id: str
    settlement_utr: str
    payment_id: str
    order_id: str
    method: str
    anomaly_type: str = ""

    @property
    def amount_inr(self) -> float:
        return round(self.amount_paise / 100.0, 2)


@dataclass
class BankCredit:
    bank_credit_id: str
    settlement_id: str
    utr: str
    credit_date: str
    credit_year: int
    amount_paise: int
    currency: str
    bank_status: str
    reference: str

    @property
    def amount_inr(self) -> float:
        return round(self.amount_paise / 100.0, 2)


@dataclass
class FeeContract:
    contract_id: str
    merchant_id: str
    provider: str
    fee_type: str
    contracted_rate: float
    currency: str
    effective_from: str
    effective_to: str
    notes: str


@dataclass
class EvidenceItem:
    evidence_id: str
    source_record_id: str
    reference_id: str
    date: str
    method: str
    gross_amount_paise: int
    expected_value: Any
    actual_value: Any
    difference: Any
    financial_impact_paise: int
    evidence_note: str

    @property
    def gross_amount_inr(self) -> float:
        return round(self.gross_amount_paise / 100.0, 2)

    @property
    def financial_impact_inr(self) -> float:
        return round(self.financial_impact_paise / 100.0, 2)


@dataclass
class Finding:
    finding_id: str
    type: str
    status: str  # "confirmed" | "under_review" | "unsupported_reference"
    title: str
    description: str
    simple_explanation: str
    financial_impact_paise: int
    currency: str
    affected_transaction_count: int
    detected_at: str
    start_date: str
    end_date: str
    confidence: float
    root_cause_reference: str
    source_record_ids: List[str] = field(default_factory=list)
    evidence: List[EvidenceItem] = field(default_factory=list)
    verification_method_a: str = ""
    verification_method_b: str = ""
    is_verified: bool = True
    is_recovery_eligible: bool = True
    recoverable_amount_paise: int = 0
    recovery_ineligibility_reason: str = ""

    @property
    def financial_impact_inr(self) -> float:
        return round(self.financial_impact_paise / 100.0, 2)

    @property
    def recoverable_amount_inr(self) -> float:
        return round(self.recoverable_amount_paise / 100.0, 2)


@dataclass
class RecoveryRequest:
    request_id: str
    finding_id: str
    created_date: str
    resolved_date: Optional[str]
    status: str  # "submitted" | "resolved" | "under_review"
    amount_requested_paise: int
    amount_recovered_paise: int
    recipient: str
    subject: str
    summary: str
    evidence_count: int

    @property
    def amount_requested_inr(self) -> float:
        return round(self.amount_requested_paise / 100.0, 2)

    @property
    def amount_recovered_inr(self) -> float:
        return round(self.amount_recovered_paise / 100.0, 2)
