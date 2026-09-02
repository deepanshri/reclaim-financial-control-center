from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.api.period import period_or_400
from app.schemas.schemas import RecoveryRequestSchema
from app.services.financial_engine import financial_engine

router = APIRouter(prefix="/recovery-requests", tags=["Recovery Requests"])


@router.get("", response_model=List[RecoveryRequestSchema], summary="List Recovery Requests")
def get_recovery_requests(
    period: Optional[str] = Query(None, description="Filter by period (e.g. 2026_H2, 2024_H2)"),
    status: Optional[str] = Query(None, description="Filter status (e.g. submitted, resolved)"),
) -> List[RecoveryRequestSchema]:
    requests = financial_engine.get_recovery_requests(period=period_or_400(period), status=status)
    return [
        RecoveryRequestSchema(
            request_id=r.request_id,
            finding_id=r.finding_id,
            anomaly_id=r.finding_id,
            created_date=r.created_date,
            resolved_date=r.resolved_date,
            status=r.status,
            amount_requested=r.amount_requested_inr,
            amount_recovered=r.amount_recovered_inr,
            recipient=r.recipient,
            subject=r.subject,
            summary=r.summary,
            evidence_count=r.evidence_count,
        )
        for r in requests
    ]


@router.get("/{request_id}", response_model=RecoveryRequestSchema, summary="Get Recovery Request by ID")
def get_recovery_request_by_id(
    request_id: str,
    period: Optional[str] = Query(None, description="Optional period key to narrow search"),
) -> RecoveryRequestSchema:
    r = financial_engine.get_recovery_request_by_id(request_id, period=period)
    if not r:
        raise HTTPException(status_code=404, detail=f"Recovery request with ID '{request_id}' not found")

    return RecoveryRequestSchema(
        request_id=r.request_id,
        finding_id=r.finding_id,
        anomaly_id=r.finding_id,
        created_date=r.created_date,
        resolved_date=r.resolved_date,
        status=r.status,
        amount_requested=r.amount_requested_inr,
        amount_recovered=r.amount_recovered_inr,
        recipient=r.recipient,
        subject=r.subject,
        summary=r.summary,
        evidence_count=r.evidence_count,
    )
