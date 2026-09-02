import csv
import io
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import quote
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, get_current_user
from app.api.period import period_or_400
from app.core.money import paise_to_inr
from app.db import operational as store
from app.models.domain import RecoveryRequest
from app.services.financial_engine import financial_engine

router = APIRouter(tags=["Workspace"])


class RecoveryCreateRequest(BaseModel):
    period: str = Field(min_length=4, max_length=16)
    finding_id: Optional[str] = None
    recipient: str = Field(default="Razorpay Support", max_length=200)
    subject: Optional[str] = Field(default=None, max_length=300)
    summary: str = Field(min_length=8, max_length=8000)
    claim_scope: str = Field(default="period", pattern="^(period|finding)$")


class SettingsPayload(BaseModel):
    fee_variance_percent: str = Field(default="0.10", max_length=16)
    sla_delay_threshold_hours: str = Field(default="24", max_length=8)
    auto_dispute_threshold: str = Field(default="1000", max_length=16)
    notification_email: str = Field(default="", max_length=200)
    razorpay_connected: bool = True


class SupportTicketRequest(BaseModel):
    subject: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=8, max_length=8000)


class AuditRequest(BaseModel):
    period: Optional[str] = None


def _csv_response(filename: str, header: list[str], rows: list[list[str]]) -> Response:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    writer.writerows(rows)
    payload = buffer.getvalue().encode("utf-8-sig")
    return Response(
        content=payload,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=\"{quote(filename)}\""},
    )


def _simple_pdf(title: str, lines: list[str]) -> bytes:
    def escape(text: str) -> str:
        return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    content_ops = ["BT", "/F1 14 Tf", "50 780 Td", f"({escape(title)}) Tj", "/F1 10 Tf", "0 -24 Td"]
    for line in lines[:48]:
        content_ops.append(f"({escape(line[:110])}) Tj")
        content_ops.append("0 -14 Td")
    content_ops.append("ET")
    stream = "\n".join(content_ops).encode("latin-1", errors="replace")
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n",
        b"4 0 obj << /Length " + str(len(stream)).encode() + b" >> stream\n" + stream + b"\nendstream endobj\n",
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
    ]
    header = b"%PDF-1.4\n"
    body = b"".join(objects)
    offsets = [0]
    cursor = len(header)
    for obj in objects:
        offsets.append(cursor)
        cursor += len(obj)
    xref_start = cursor
    xref = [b"xref\n0 6\n0000000000 65535 f \n"]
    for offset in offsets[1:]:
        xref.append(f"{offset:010d} 00000 n \n".encode())
    trailer = (
        b"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n"
        + str(xref_start).encode()
        + b"\n%%EOF\n"
    )
    return header + body + b"".join(xref) + trailer


@router.post("/recovery-requests")
def create_recovery_request(
    payload: RecoveryCreateRequest,
    user: CurrentUser = Depends(get_current_user),
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
):
    period = period_or_400(payload.period)
    status_data = financial_engine.get_financial_status(period=period)
    findings = [f for f in financial_engine.get_findings(period=period) if f.status == "confirmed"]
    eligible = [f for f in findings if f.is_recovery_eligible and f.recoverable_amount_paise > 0]

    if payload.claim_scope == "finding":
        if not payload.finding_id:
            raise HTTPException(status_code=400, detail="finding_id is required for a single-finding claim.")
        finding = financial_engine.get_finding_by_id(payload.finding_id, period=period)
        if not finding:
            raise HTTPException(status_code=404, detail="Finding not found for this merchant period.")
        if not finding.is_recovery_eligible:
            raise HTTPException(status_code=400, detail="This finding is not recovery-eligible.")
        existing_for_finding = [
            r for r in financial_engine.get_recovery_requests(period=period) if r.finding_id == finding.finding_id
        ]
        already_paise = sum(r.amount_requested_paise for r in existing_for_finding)
        amount_paise = max(0, finding.recoverable_amount_paise - already_paise)
        finding_id = finding.finding_id
        subject = payload.subject or finding.title
    else:
        if not eligible:
            raise HTTPException(status_code=400, detail="No recovery-eligible findings in this period.")
        existing = financial_engine.get_recovery_requests(period=period)
        already_paise = sum(r.amount_requested_paise for r in existing)
        amount_paise = max(0, sum(f.recoverable_amount_paise for f in eligible) - already_paise)
        finding_id = "period_combined"
        subject = payload.subject or f"Combined recovery claim for {period.replace('_', ' ')}"

    if amount_paise <= 0:
        raise HTTPException(
            status_code=400,
            detail="A recovery claim covering this eligible amount is already on file.",
        )

    if idempotency_key:
        existing = store.get_recovery_by_idempotency(user.merchant_id, idempotency_key)
        if existing:
            return {
                "request_id": existing["request_id"],
                "finding_id": existing["finding_id"],
                "status": existing["status"],
                "amount_requested": paise_to_inr(existing["amount_requested_paise"]),
                "amount_recovered": paise_to_inr(existing["amount_recovered_paise"]),
                "idempotent_replay": True,
            }

    request_id = f"REQ-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"
    created = datetime.now(timezone.utc).date().isoformat()
    record = {
        "request_id": request_id,
        "merchant_id": user.merchant_id,
        "period_key": period,
        "finding_id": finding_id,
        "created_date": created,
        "resolved_date": None,
        "status": "submitted",
        "amount_requested_paise": int(amount_paise),
        "amount_recovered_paise": 0,
        "recipient": payload.recipient.strip() or "Razorpay Support",
        "subject": subject[:300],
        "summary": payload.summary.strip(),
        "evidence_count": min(sum(len(f.evidence) for f in (eligible if payload.claim_scope == "period" else [finding])), 99),
        "idempotency_key": idempotency_key,
    }
    try:
        store.insert_recovery_request(record)
    except ValueError:
        raise HTTPException(status_code=409, detail="A recovery request with this idempotency key already exists.")

    return {
        "request_id": request_id,
        "finding_id": finding_id,
        "anomaly_id": finding_id,
        "created_date": created,
        "resolved_date": None,
        "status": "submitted",
        "amount_requested": paise_to_inr(amount_paise),
        "amount_recovered": 0.0,
        "recipient": record["recipient"],
        "subject": record["subject"],
        "summary": record["summary"],
        "evidence_count": record["evidence_count"],
        "period": period,
        "money_affected_inr": status_data["money_affected_inr"],
        "potential_recovery_inr": paise_to_inr(amount_paise),
    }


@router.get("/exports/statement.csv")
def export_statement_csv(
    period: Optional[str] = Query(None),
    user: CurrentUser = Depends(get_current_user),
):
    period_key = period_or_400(period)
    items, total, _summary = financial_engine.get_statement_ledger(period=period_key, page=1, page_size=10000)
    rows = [
        [item["date"], item["transaction_id"], item["type"], item["status"], item["method"], f"{item['amount']:.2f}"]
        for item in items
    ]
    _ = user
    return _csv_response(
        f"reclaim-statement-{period_key}.csv",
        ["date", "transaction_id", "type", "status", "method", "amount_inr"],
        rows,
    )


@router.get("/exports/report.pdf")
def export_report_pdf(
    period: Optional[str] = Query(None),
    user: CurrentUser = Depends(get_current_user),
):
    period_key = period_or_400(period)
    status_data = financial_engine.get_financial_status(period=period_key)
    months = financial_engine.get_monthly_reports(period=period_key)
    lines = [
        f"Merchant: {user.merchant_name} ({user.merchant_id})",
        f"Period: {status_data['period_label']}",
        f"Dataset: synthetic demo — not live gateway data",
        f"Money affected (INR): {status_data['money_affected_inr']:.2f}",
        f"Potential recovery (INR): {status_data['potential_recovery_inr']:.2f}",
        f"Health score: {status_data['health_score']}",
        f"Severity: {status_data['severity_label']}",
        "",
        "Monthly breakdown:",
    ]
    for month in months:
        lines.append(
            f"{month['month']}  volume {month['gross_volume_inr']:.2f}  "
            f"loss {month['loss_detected_inr']:.2f}  recovered {month['amount_recovered_inr']:.2f}"
        )
    payload = _simple_pdf(f"Reclaim period report {period_key}", lines)
    return Response(
        content=payload,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=\"reclaim-report-{period_key}.pdf\""},
    )


@router.get("/settings")
def get_settings(user: CurrentUser = Depends(get_current_user)) -> dict:
    stored = store.get_settings_payload(user.merchant_id) or {
        "fee_variance_percent": "0.10",
        "sla_delay_threshold_hours": "24",
        "auto_dispute_threshold": "1000",
        "notification_email": "finance@zenzocommerce.in",
        "razorpay_connected": True,
    }
    return stored


@router.put("/settings")
def put_settings(payload: SettingsPayload, user: CurrentUser = Depends(get_current_user)) -> dict:
    saved = store.save_settings_payload(user.merchant_id, payload.model_dump())
    return saved


@router.post("/support/tickets")
def create_support_ticket(payload: SupportTicketRequest, user: CurrentUser = Depends(get_current_user)) -> dict:
    ticket_id = f"TCK-{uuid4().hex[:8].upper()}"
    saved = store.insert_support_ticket(ticket_id, user.merchant_id, payload.subject.strip(), payload.description.strip())
    return {**saved, "merchant_id": user.merchant_id}


@router.post("/audits")
def run_audit(payload: AuditRequest, user: CurrentUser = Depends(get_current_user)) -> dict:
    period_key = period_or_400(payload.period)
    financial_engine.rerun_period(period_key)
    findings = financial_engine.get_findings(period=period_key)
    run = store.insert_audit_run(f"AUD-{uuid4().hex[:8].upper()}", user.merchant_id, period_key, len(findings))
    status_data = financial_engine.get_financial_status(period=period_key)
    return {
        **run,
        "merchant_id": user.merchant_id,
        "money_affected_inr": status_data["money_affected_inr"],
        "potential_recovery_inr": status_data["potential_recovery_inr"],
        "confirmed_finding_count": status_data["confirmed_finding_count"],
    }
