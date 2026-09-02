from typing import Optional
from fastapi import APIRouter, Query
from app.api.period import period_or_400
from app.schemas.schemas import (
    DashboardFindingSummary,
    DashboardResponse,
    FinancialStatusSchema,
    PeriodInfo,
)
from app.services.financial_engine import financial_engine

router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard", response_model=DashboardResponse, summary="Dashboard Overview & Health")
def get_dashboard(
    period: Optional[str] = Query(None, description="Audit period key (e.g. 2026_H2, 2025_H1, 2024_H1)"),
    year: Optional[int] = Query(None, description="Filter year (e.g. 2026, 2025, 2024)"),
) -> DashboardResponse:
    period_key = period_or_400(period, year)
    status_data = financial_engine.get_financial_status(period=period_key)
    all_findings = financial_engine.get_findings(period=period_key)

    confirmed_summaries: list[DashboardFindingSummary] = []
    under_review_summaries: list[DashboardFindingSummary] = []

    for f in all_findings:
        summary = DashboardFindingSummary(
            finding_id=f.finding_id,
            anomaly_id=f.finding_id,
            type=f.type,
            status=f.status,
            title=f.title,
            description=f.description,
            simple_explanation=f.simple_explanation,
            financial_impact_inr=f.financial_impact_inr,
            recoverable_amount_inr=f.recoverable_amount_inr,
            is_recovery_eligible=f.is_recovery_eligible,
            recovery_ineligibility_reason=f.recovery_ineligibility_reason,
            affected_transaction_count=f.affected_transaction_count,
            affected_transactions=f.affected_transaction_count,
            detected_at=f.detected_at,
            confidence=f.confidence,
        )
        if f.status == "confirmed":
            confirmed_summaries.append(summary)
        else:
            under_review_summaries.append(summary)

    financial_status = FinancialStatusSchema(**status_data)
    available_periods = [PeriodInfo(**p) for p in financial_engine.get_available_periods()]

    period_str = status_data.get("period", "2026_H2")
    return DashboardResponse(
        financial_status=financial_status,
        confirmed_findings=confirmed_summaries,
        under_review_findings=under_review_summaries,
        available_periods=available_periods,
        last_synced=f"Synthetic demo records for {period_str} — not a live Razorpay connection",
    )
