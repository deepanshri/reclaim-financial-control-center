from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# Base & Health
# -----------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str = "ok"
    version: Optional[str] = None
    service: Optional[str] = None
    dataset_status: Optional[str] = None
    environment: Optional[str] = None


# -----------------------------------------------------------------------------
# Merchant & Periods
# -----------------------------------------------------------------------------

class DatasetPeriod(BaseModel):
    start: str
    end: str
    years: List[int]


class ContractInfo(BaseModel):
    fee_rate: float
    effective_from: str
    effective_to: str


class MerchantInfo(BaseModel):
    merchant_name: str
    merchant_id: str
    currency: str
    payment_provider: str
    dataset_period: DatasetPeriod
    contract: ContractInfo
    demo_status: str
    dataset_type: Optional[str] = None
    finance_email: Optional[str] = None
    settlement_bank: Optional[str] = None
    initials: Optional[str] = None
    notes: Optional[str] = None


class PeriodInfo(BaseModel):
    key: str
    label: str
    year: int
    half: str
    start: str
    end: str
    review_status: str  # internal: "healthy" | "needs_review" | "action_needed" | "action_required"
    severity_level: Optional[str] = "healthy"  # internal key; merchant label is severity_label
    severity_label: Optional[str] = "MONITOR"  # MONITOR | ACTION NEEDED | URGENT ACTION
    severity_message: Optional[str] = "Your payments are in good shape."
    is_action_required: bool
    confirmed_finding_count: int = 0
    confirmed_loss_inr: float = 0.0


class DatasetStatusResponse(BaseModel):
    merchant_name: str
    payment_provider: str
    dataset_start_date: str
    dataset_end_date: str
    payment_record_count: int
    refund_record_count: int
    settlement_record_count: int
    reconciliation_record_count: int
    confirmed_anomaly_count: int
    under_review_anomaly_count: int
    recovery_request_count: int


class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    data: List[Any]


# -----------------------------------------------------------------------------
# Financial Status & Dashboard
# -----------------------------------------------------------------------------

class FinancialStatusSchema(BaseModel):
    period: Optional[str] = None
    period_label: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    year: Optional[int] = None
    currency: str = "INR"
    total_payment_volume_inr: float
    total_fees_inr: float
    total_refunds_inr: float
    total_settlements_inr: float
    confirmed_loss_inr: float
    money_affected_inr: Optional[float] = None
    potential_recovery_inr: Optional[float] = None
    potential_loss_inr: float = Field(
        description="Compatibility alias of potential_recovery_inr. Not Money Affected.",
    )
    recovery_requested_inr: float
    recovered_inr: float
    recovery_requests_count: int = 0
    recovery_requested_amount: float = 0.0
    recovered_requests_count: int = 0
    recovered_amount: float = 0.0
    under_review_count: int = 0
    under_review_amount: float = 0.0
    under_review_inr: float = 0.0
    not_recovered_count: int = 0
    not_recovered_amount: float = 0.0
    not_recovered_inr: float = 0.0
    confirmed_finding_count: int
    under_review_finding_count: int
    total_finding_count: int
    health_score: int
    severity_level: Optional[str] = "healthy"
    severity_label: Optional[str] = "MONITOR"
    severity_message: Optional[str] = "A small difference was found, but no immediate action is needed."
    is_action_required: bool = False
    review_status: str = "review"


class DashboardFindingSummary(BaseModel):
    finding_id: str
    anomaly_id: Optional[str] = None
    type: str
    status: str
    title: str
    description: str
    simple_explanation: str
    financial_impact_inr: float
    recoverable_amount_inr: Optional[float] = None
    is_recovery_eligible: Optional[bool] = True
    recovery_ineligibility_reason: Optional[str] = ""
    affected_transaction_count: int
    affected_transactions: Optional[int] = None
    detected_at: str
    confidence: float


class DashboardResponse(BaseModel):
    financial_status: FinancialStatusSchema
    confirmed_findings: List[DashboardFindingSummary]
    under_review_findings: List[DashboardFindingSummary]
    available_periods: Optional[List[PeriodInfo]] = None
    last_synced: str = "Synthetic demo data validated from period records"


# -----------------------------------------------------------------------------
# Findings & Evidence
# -----------------------------------------------------------------------------

class EvidenceItemSchema(BaseModel):
    evidence_id: str
    source_record_id: str
    transaction_id: Optional[str] = None
    reference_id: str
    date: str
    method: str
    gross_amount: float
    expected_value: Any
    actual_value: Any
    difference: Any
    financial_impact: float
    evidence_note: str


class FindingSchema(BaseModel):
    finding_id: str
    anomaly_id: str
    type: str
    status: str
    title: str
    description: str
    simple_explanation: str
    financial_impact: float
    recoverable_amount: Optional[float] = None
    recoverable_amount_inr: Optional[float] = None
    is_recovery_eligible: Optional[bool] = True
    recovery_ineligibility_reason: Optional[str] = ""
    currency: str
    affected_transaction_count: int
    affected_transactions: int
    detected_at: str
    start_date: str
    end_date: str
    confidence: float
    root_cause_reference: str
    source_record_ids: List[str]
    evidence_count: int
    evidence: Optional[List[EvidenceItemSchema]] = None
    evidence_logs: Optional[List[EvidenceItemSchema]] = None
    verification_method_a: Optional[str] = None
    verification_method_b: Optional[str] = None
    is_verified: bool = True


class FindingEvidenceResponse(BaseModel):
    finding_id: str
    anomaly_id: Optional[str] = None
    title: str
    financial_impact: float
    evidence_count: int
    evidence: List[EvidenceItemSchema]
    evidence_logs: Optional[List[EvidenceItemSchema]] = None


# -----------------------------------------------------------------------------
# Recovery Requests
# -----------------------------------------------------------------------------

class RecoveryRequestSchema(BaseModel):
    request_id: str
    finding_id: str
    anomaly_id: Optional[str] = None
    created_date: str
    resolved_date: Optional[str] = None
    status: str
    amount_requested: float
    amount_recovered: float
    recipient: str
    subject: str
    summary: str
    evidence_count: int


# -----------------------------------------------------------------------------
# Statement & Activity
# -----------------------------------------------------------------------------

class StatementActivityItem(BaseModel):
    id: str
    date: str
    timestamp: int
    transaction_id: str
    type: str
    status: str
    amount: float
    is_negative: bool
    fee_rate: Optional[str] = None
    method: str


class StatementSummary(BaseModel):
    total_payments_inr: float
    fees_deducted_inr: float
    bank_deposits_inr: float
    matching_rate_percent: float


class StatementResponse(BaseModel):
    items: List[StatementActivityItem]
    total: int
    page: int
    page_size: int
    summary: StatementSummary
    period: Optional[str] = None


# -----------------------------------------------------------------------------
# Reports
# -----------------------------------------------------------------------------

class MonthlyReportItem(BaseModel):
    month: str
    transaction_count: int
    gross_volume_inr: float
    fees_inr: float
    refunds_inr: float
    settlements_inr: float
    loss_detected_inr: float
    amount_recovered_inr: float


class ReportsResponse(BaseModel):
    period: Optional[str] = None
    year: Optional[int] = None
    monthly_breakdown: List[MonthlyReportItem]
    total_gross_volume_inr: float
    total_fees_inr: float
    total_refunds_inr: float
    total_settlements_inr: float
    total_loss_detected_inr: float
    total_amount_recovered_inr: float
