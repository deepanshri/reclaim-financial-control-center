from typing import Optional
from fastapi import APIRouter, Query
from app.api.period import period_or_400
from app.schemas.schemas import MonthlyReportItem, ReportsResponse
from app.services.financial_engine import financial_engine

router = APIRouter(prefix="/reports", tags=["Reports & Analytics"])


@router.get("", response_model=ReportsResponse, summary="Get Historical Performance & Recovery Reports")
def get_reports(
    period: Optional[str] = Query(None, description="Filter by period (e.g. 2026_H2, 2025_H1)"),
    year: Optional[int] = Query(None, description="Filter report year (2026, 2025, 2024)"),
) -> ReportsResponse:
    period_key = period_or_400(period, year)
    monthly_data = financial_engine.get_monthly_reports(period=period_key)
    items = [MonthlyReportItem(**m) for m in monthly_data]

    total_vol = sum(m["gross_volume_inr"] for m in monthly_data)
    total_fees = sum(m["fees_inr"] for m in monthly_data)
    total_refunds = sum(m["refunds_inr"] for m in monthly_data)
    total_settlements = sum(m["settlements_inr"] for m in monthly_data)
    total_losses = sum(m["loss_detected_inr"] for m in monthly_data)
    total_recovered = sum(m["amount_recovered_inr"] for m in monthly_data)

    yr_int = int(period_key[:4])

    return ReportsResponse(
        period=period_key,
        year=yr_int,
        monthly_breakdown=items,
        total_gross_volume_inr=round(total_vol, 2),
        total_fees_inr=round(total_fees, 2),
        total_refunds_inr=round(total_refunds, 2),
        total_settlements_inr=round(total_settlements, 2),
        total_loss_detected_inr=round(total_losses, 2),
        total_amount_recovered_inr=round(total_recovered, 2),
    )
