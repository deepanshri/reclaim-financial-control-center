from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.api.period import period_or_400
from app.schemas.schemas import EvidenceItemSchema, FindingEvidenceResponse, FindingSchema
from app.services.financial_engine import financial_engine

router = APIRouter(prefix="/anomalies", tags=["Anomalies & Findings"])


def _map_evidence(ev_list) -> List[EvidenceItemSchema]:
    return [
        EvidenceItemSchema(
            evidence_id=ev.evidence_id,
            source_record_id=ev.source_record_id,
            transaction_id=ev.source_record_id,
            reference_id=ev.reference_id,
            date=ev.date,
            method=ev.method,
            gross_amount=ev.gross_amount_inr,
            expected_value=ev.expected_value,
            actual_value=ev.actual_value,
            difference=ev.difference,
            financial_impact=ev.financial_impact_inr,
            evidence_note=ev.evidence_note,
        )
        for ev in ev_list
    ]


# The list response is a summary. Detail routes still return every record id.
LIST_SOURCE_ID_CAP = 25


def _map_finding(f, include_evidence: bool = True) -> FindingSchema:
    ev_schemas = _map_evidence(f.evidence) if include_evidence else []
    source_ids = (
        f.source_record_ids
        if include_evidence
        else f.source_record_ids[:LIST_SOURCE_ID_CAP]
    )
    return FindingSchema(
        finding_id=f.finding_id,
        anomaly_id=f.finding_id,
        type=f.type,
        status=f.status,
        title=f.title,
        description=f.description,
        simple_explanation=f.simple_explanation,
        financial_impact=f.financial_impact_inr,
        recoverable_amount=f.recoverable_amount_inr,
        recoverable_amount_inr=f.recoverable_amount_inr,
        is_recovery_eligible=f.is_recovery_eligible,
        recovery_ineligibility_reason=f.recovery_ineligibility_reason,
        currency=f.currency,
        affected_transaction_count=f.affected_transaction_count,
        affected_transactions=f.affected_transaction_count,
        detected_at=f.detected_at,
        start_date=f.start_date,
        end_date=f.end_date,
        confidence=f.confidence,
        root_cause_reference=f.root_cause_reference,
        source_record_ids=source_ids,
        evidence_count=len(f.evidence),
        evidence=ev_schemas if include_evidence else None,
        evidence_logs=ev_schemas if include_evidence else None,
        verification_method_a=f.verification_method_a,
        verification_method_b=f.verification_method_b,
        is_verified=f.is_verified,
    )


@router.get("", response_model=List[FindingSchema], summary="List Detected Anomalies / Findings")
def get_anomalies(
    period: Optional[str] = Query(None, description="Filter by period (e.g. 2026_H2, 2025_H1, 2024_H1)"),
    year: Optional[int] = Query(None, description="Filter audit year (e.g. 2026, 2025, 2024)"),
    status: Optional[str] = Query(None, description="Filter status (e.g. confirmed, under_review)"),
) -> List[FindingSchema]:
    findings = financial_engine.get_findings(period=period_or_400(period, year), status=status)
    return [_map_finding(f, include_evidence=False) for f in findings]


@router.get("/{finding_id}", response_model=FindingSchema, summary="Get Finding Details by ID")
def get_anomaly_by_id(
    finding_id: str,
    period: Optional[str] = Query(None, description="Optional period key to narrow search"),
) -> FindingSchema:
    f = financial_engine.get_finding_by_id(finding_id, period=period)
    if not f:
        raise HTTPException(status_code=404, detail=f"Finding with ID '{finding_id}' not found")
    return _map_finding(f)


@router.get("/{finding_id}/evidence", response_model=FindingEvidenceResponse, summary="Get Finding Evidence Logs")
def get_anomaly_evidence(
    finding_id: str,
    period: Optional[str] = Query(None, description="Optional period key to narrow search"),
) -> FindingEvidenceResponse:
    f = financial_engine.get_finding_by_id(finding_id, period=period)
    if not f:
        raise HTTPException(status_code=404, detail=f"Finding with ID '{finding_id}' not found")

    ev_schemas = _map_evidence(f.evidence)
    return FindingEvidenceResponse(
        finding_id=f.finding_id,
        anomaly_id=f.finding_id,
        title=f.title,
        financial_impact=f.financial_impact_inr,
        evidence_count=len(ev_schemas),
        evidence=ev_schemas,
        evidence_logs=ev_schemas,
    )
