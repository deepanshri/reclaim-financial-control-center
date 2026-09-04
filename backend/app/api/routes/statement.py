from typing import Optional
from fastapi import APIRouter, Query
from app.api.period import period_or_400
from app.schemas.schemas import StatementActivityItem, StatementResponse, StatementSummary
from app.services.financial_engine import financial_engine

router = APIRouter(tags=["Statement"])


@router.get("/statement", response_model=StatementResponse, summary="Statement Activity Stream")
def get_statement(
    period: Optional[str] = Query(None, description="Filter by period (e.g. 2026_H2, 2024_H1)"),
    year: Optional[int] = Query(None, description="Filter by year (2026, 2025, 2024)"),
    month: Optional[str] = Query(None, description="Filter by month (e.g. 2026-07)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    q: Optional[str] = Query(None, description="Search transaction id or date"),
    type: Optional[str] = Query(None, description="Filter by ledger type (Payment, Fee, Bank Deposit, Refund)"),
) -> StatementResponse:
    period_key = period_or_400(period, year)
    items_raw, total, summary_raw = financial_engine.get_statement_ledger(
        period=period_key,
        year=year,
        month=month,
        page=page,
        page_size=page_size,
        search=q,
        txn_type=type,
    )

    items = [StatementActivityItem(**item) for item in items_raw]
    summary = StatementSummary(**summary_raw)

    return StatementResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        summary=summary,
        period=period_key,
    )
