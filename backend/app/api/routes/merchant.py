from typing import Optional
from fastapi import APIRouter, Query
from app.api.period import period_or_400
from app.schemas.schemas import MerchantInfo
from app.services.data_repository import data_repository

router = APIRouter(tags=["Merchant & Profile"])


@router.get("/merchant", response_model=MerchantInfo, summary="Get Merchant Profile Info")
def get_merchant_profile(
    period: Optional[str] = Query(None, description="Period key e.g. 2026_H2"),
) -> MerchantInfo:
    merchant_data = data_repository.get_merchant_data(period=period_or_400(period))
    return MerchantInfo(**merchant_data)


@router.get("/profile", response_model=MerchantInfo, summary="Get Merchant Profile Info (Alias)")
def get_profile(
    period: Optional[str] = Query(None, description="Period key e.g. 2026_H2"),
) -> MerchantInfo:
    merchant_data = data_repository.get_merchant_data(period=period_or_400(period))
    return MerchantInfo(**merchant_data)
