import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.deps import get_current_user
from app.api.routes import (
    anomalies,
    auth,
    dashboard,
    dataset,
    health,
    merchant,
    payments,
    recovery_requests,
    refunds,
    reports,
    settlements,
    statement,
    workspace,
)
from app.core.config import settings
from app.core.exceptions import InvalidPeriodError
from app.core.rate_limit import enforce_rate_limit
from app.db import operational as operational_store

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s %(message)s",
)
logger = logging.getLogger("reclaim.api")


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True


logging.getLogger().addFilter(_RequestIdFilter())


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Reclaim Financial Control Center API...")
    try:
        operational_store.initialize()
        logger.info("Operational store ready. Period datasets load on first financial request.")
    except Exception as e:
        logger.critical("FATAL: Unexpected error initializing operational store: %s", e)
        raise e

    yield

    logger.info("Shutting down Reclaim API.")


app = FastAPI(
    title="Reclaim AI — Financial Control Center API",
    description="Settlement auditor API. Synthetic demo data unless a live gateway is connected.",
    version="1.1.0",
    docs_url="/docs" if settings.enable_docs else None,
    redoc_url="/redoc" if settings.enable_docs else None,
    openapi_url="/openapi.json" if settings.enable_docs else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "Accept"],
)


SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "X-Robots-Tag": "noindex, nofollow",
}


def _apply_security_headers(response) -> None:
    for header, value in SECURITY_HEADERS.items():
        response.headers.setdefault(header, value)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
    request.state.request_id = request_id
    try:
        await enforce_rate_limit(request)
    except HTTPException as exc:
        limited = JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "request_id": request_id},
            headers={"X-Request-ID": request_id, "Retry-After": "60"},
        )
        _apply_security_headers(limited)
        return limited
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    _apply_security_headers(response)
    return response


@app.exception_handler(InvalidPeriodError)
async def invalid_period_handler(request: Request, exc: InvalidPeriodError):
    return JSONResponse(
        status_code=400,
        content={
            "detail": {
                "code": "invalid_period",
                "message": f"Unknown period '{exc.period}'.",
                "valid_periods": exc.valid,
            },
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return await http_exception_handler(request, exc)
    logger.exception("Unhandled server error")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "The financial service could not complete this request. Please try again.",
            "request_id": getattr(request.state, "request_id", None),
        },
    )


protected = [Depends(get_current_user)]

app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api", dependencies=protected)
app.include_router(statement.router, prefix="/api", dependencies=protected)
app.include_router(anomalies.router, prefix="/api", dependencies=protected)
app.include_router(recovery_requests.router, prefix="/api", dependencies=protected)
app.include_router(reports.router, prefix="/api", dependencies=protected)
app.include_router(merchant.router, prefix="/api", dependencies=protected)
app.include_router(dataset.router, prefix="/api", dependencies=protected)
app.include_router(payments.router, prefix="/api", dependencies=protected)
app.include_router(refunds.router, prefix="/api", dependencies=protected)
app.include_router(settlements.router, prefix="/api", dependencies=protected)
app.include_router(workspace.router, prefix="/api", dependencies=protected)


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "Reclaim AI — Financial Control Center API",
        "version": "1.1.0",
        "docs": "/docs" if settings.enable_docs else None,
        "health": "/api/health",
        "login": "/api/auth/login",
        "dataset_type": "synthetic_demo",
    }
