import math
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query

from app.api.period import period_or_400
from app.schemas import PaginatedResponse
from app.services.data_loader import data_loader

router = APIRouter()

PII_KEYS = {"email", "contact", "phone", "customer_email", "customer_contact"}


def _redact(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    cleaned = []
    for row in rows:
        cleaned.append({key: value for key, value in row.items() if key.lower() not in PII_KEYS})
    return cleaned


@router.get("/payments", response_model=PaginatedResponse, tags=["Payments"])
async def get_payments(
    period: Optional[str] = Query(None, description="Period key e.g. 2026_H2"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=500, description="Number of items per page"),
    year: Optional[int] = Query(None, description="Filter by year (e.g. 2026, 2025, 2024)"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    anomaly_type: Optional[str] = Query(None, description="Filter by anomaly tag (e.g. fee_rate_increase)"),
):
    period_key = period_or_400(period, year)
    data, total = data_loader.get_payments(
        period=period_key,
        page=page,
        page_size=page_size,
        year=year,
        start_date=start_date,
        end_date=end_date,
        anomaly_type=anomaly_type,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        data=_redact(data),
    )
