from typing import List, Optional
from fastapi import APIRouter, Query
from app.api.period import period_or_400
from app.schemas.schemas import DatasetStatusResponse, PeriodInfo
from app.services.data_loader import data_loader
from app.services.financial_engine import financial_engine

router = APIRouter(tags=["Dataset"])


@router.get("/dataset/status", response_model=DatasetStatusResponse)
async def get_dataset_status(
    period: Optional[str] = Query(None, description="Period key e.g. 2026_H2"),
):
    """
    Returns real-time record counts and anomaly metrics computed directly
    from the validated Reclaim dataset files.
    """
    period_key = period_or_400(period)
    status_data = data_loader.get_dataset_status(period=period_key)
    engine_status = financial_engine.get_financial_status(period=period_key)
    status_data["confirmed_anomaly_count"] = engine_status["confirmed_finding_count"]
    status_data["under_review_anomaly_count"] = engine_status["under_review_finding_count"]
    return DatasetStatusResponse(**status_data)


@router.get("/dataset/periods", response_model=List[PeriodInfo])
@router.get("/periods", response_model=List[PeriodInfo])
async def get_periods():
    """
    Returns dynamically computed status (healthy vs action_required)
    and metadata for all six half-year periods.
    """
    periods_data = financial_engine.get_available_periods()
    return [PeriodInfo(**p) for p in periods_data]
