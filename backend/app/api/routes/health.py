from fastapi import APIRouter

from app.core.config import settings
from app.schemas.schemas import HealthResponse
from app.services.data_repository import data_repository

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="Service Health Check")
def get_health() -> HealthResponse:
    loaded = data_repository.is_loaded
    return HealthResponse(
        status="ok",
        version="1.1.0",
        service="reclaim-financial-engine",
        dataset_status="loaded" if loaded else "not_loaded",
        environment=settings.environment,
    )
