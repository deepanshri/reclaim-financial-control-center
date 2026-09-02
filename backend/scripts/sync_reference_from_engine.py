"""
Recompute loaded anomalies.csv / anomaly_evidence.csv / recovery_requests.csv
from the financial engine (source payments → detectors → eligibility).

This does not regenerate transactions. It only refreshes reference records so
stored impacts match Method B (sum of actual − contracted values), not the
old Method A gross × rate-diff approximation.
"""
from __future__ import annotations

import csv
from pathlib import Path

from app.models.domain import Finding, RecoveryRequest
from app.services.data_repository import DataRepository
from app.services.financial_engine import FinancialEngine

DATA_ROOT = Path(__file__).resolve().parent.parent / "data" / "reclaim_six_half_year_datasets"
PERIODS = ["2024_H1", "2024_H2", "2025_H1", "2025_H2", "2026_H1", "2026_H2"]


def _inr(paise: int) -> str:
    return f"{paise / 100.0:.2f}"


def _inr_words(amount: float) -> str:
    return f"INR {amount:,.2f}"


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def _sync_anomalies(p_dir: Path, findings: list[Finding]) -> dict[str, Finding]:
    path = p_dir / "anomalies.csv"
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    by_id = {f.finding_id: f for f in findings}
    for row in rows:
        finding = by_id.get(row["anomaly_id"])
        if finding is None:
            continue
        row["affected_transactions"] = str(finding.affected_transaction_count)
        row["financial_impact"] = _inr(finding.financial_impact_paise)
        row["is_recovery_eligible"] = "true" if finding.is_recovery_eligible else "false"
        row["recoverable_amount"] = _inr(finding.recoverable_amount_paise)
        row["recovery_ineligibility_reason"] = finding.recovery_ineligibility_reason or ""
        if finding.start_date:
            row["start_date"] = finding.start_date
        if finding.end_date:
            row["end_date"] = finding.end_date
        if finding.detected_at:
            row["detected_date"] = finding.detected_at
        if finding.type != "settlement_delay":
            if finding.verification_method_a:
                row["verification_method_a"] = finding.verification_method_a
            if finding.verification_method_b:
                row["verification_method_b"] = finding.verification_method_b
        if finding.root_cause_reference:
            row["root_cause"] = finding.root_cause_reference
        if finding.type == "missing_settlement" and finding.source_record_ids:
            pay_id = finding.source_record_ids[0]
            row["expected_value"] = _inr_words(finding.financial_impact_inr)
            row["actual_value"] = "INR 0.00"
            row["root_cause"] = (
                f"Payment {pay_id} was captured on {finding.start_date} "
                "but has no matching processed settlement."
            )
        if finding.type == "fee_rate_increase":
            row["expected_value"] = "1.80%"
            row["actual_value"] = "2.30%"

    _write_csv(path, fieldnames, rows)
    return by_id


def _sync_evidence(p_dir: Path, findings: list[Finding]) -> None:
    path = p_dir / "anomaly_evidence.csv"
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        existing = list(reader)

    finding_ids = {f.finding_id for f in findings if f.evidence}
    kept = [row for row in existing if row.get("anomaly_id") not in finding_ids]
    generated: list[dict] = []
    for finding in findings:
        if not finding.evidence:
            continue
        for item in finding.evidence:
            generated.append(
                {
                    "evidence_id": item.evidence_id,
                    "anomaly_id": finding.finding_id,
                    "transaction_id": item.source_record_id,
                    "reference_id": item.reference_id,
                    "date": item.date,
                    "expected_value": str(item.expected_value),
                    "actual_value": str(item.actual_value),
                    "difference": str(item.difference),
                    "gross_amount": _inr(item.gross_amount_paise),
                    "method": item.method,
                    "evidence_note": item.evidence_note,
                }
            )
    _write_csv(path, fieldnames, kept + generated)


def _ticket_copy(request: RecoveryRequest, finding: Finding) -> tuple[str, str]:
    impact = finding.financial_impact_inr
    recoverable = finding.recoverable_amount_inr
    source = finding.source_record_ids[0] if finding.source_record_ids else finding.finding_id
    if finding.type == "fee_rate_increase":
        subject = f"Request for review of MDR fee overcharge - {finding.affected_transaction_count:,} transactions"
        summary = (
            f"Dispute filed for contracted 1.80% vs charged 2.30% MDR on "
            f"{finding.affected_transaction_count:,} payments. Engine-verified excess MDR "
            f"{_inr_words(impact)}; eligible recovery {_inr_words(recoverable)}."
        )
    elif finding.type == "duplicate_refund":
        subject = "Request for reversal of duplicate refund debit"
        summary = (
            f"Duplicate refund debit of {_inr_words(impact)} confirmed against {source}. "
            f"Eligible recovery {_inr_words(recoverable)}."
        )
    elif finding.type == "missing_settlement":
        subject = f"Request for settlement of captured payment {source}"
        summary = (
            f"Unsettled captured payment {source}: money affected {_inr_words(impact)}; "
            f"eligible net recovery {_inr_words(recoverable)}."
        )
    elif finding.type == "bank_credit_missing":
        subject = f"Request for investigation of missing bank credit - {source}"
        summary = (
            f"Processed settlement {source} has no matching bank credit. "
            f"Money affected {_inr_words(impact)}; eligible recovery {_inr_words(recoverable)}."
        )
    elif finding.type == "settlement_amount_discrepancy":
        subject = f"Request for review of settlement shortfall {source}"
        if finding.is_recovery_eligible:
            summary = (
                f"Settlement shortfall of {_inr_words(impact)} versus calculated net. "
                f"Eligible recovery {_inr_words(recoverable)}."
            )
        else:
            summary = (
                f"Claim against settlement shortfall {_inr_words(impact)} was rejected: "
                f"{finding.recovery_ineligibility_reason}"
            )
    else:
        subject = request.subject
        summary = request.summary
    if request.status.lower() in ["resolved", "recovered"] and request.amount_recovered_paise > 0:
        summary += f" Recovered {_inr_words(request.amount_recovered_paise / 100.0)}."
    elif request.status.lower() in ["under_review", "submitted", "pending"]:
        summary += " Under active review."
    return subject, summary


def _sync_requests(p_dir: Path, by_id: dict[str, Finding], existing: list[RecoveryRequest]) -> list[str]:
    path = p_dir / "recovery_requests.csv"
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    log: list[str] = []
    for row in rows:
        finding = by_id.get(row.get("anomaly_id", ""))
        if finding is None:
            continue
        old_requested = float(row.get("amount_requested") or 0)
        old_recovered = float(row.get("amount_recovered") or 0)
        if finding.is_recovery_eligible and finding.recoverable_amount_paise > 0:
            new_requested = finding.recoverable_amount_inr
        else:
            # Ineligible finding: a rejected ticket is documentation only.
            new_requested = 0.0
        new_recovered = min(old_recovered, new_requested)
        if row.get("status", "").lower() in ["rejected", "not_recovered", "failed"]:
            new_recovered = 0.0
        row["amount_requested"] = f"{new_requested:.2f}"
        row["amount_recovered"] = f"{new_recovered:.2f}"
        tmp = RecoveryRequest(
            request_id=row["request_id"],
            finding_id=row.get("anomaly_id", ""),
            created_date=row.get("created_date", ""),
            resolved_date=row.get("resolved_date") or None,
            status=row.get("status", ""),
            amount_requested_paise=int(round(new_requested * 100)),
            amount_recovered_paise=int(round(new_recovered * 100)),
            recipient=row.get("recipient", ""),
            subject=row.get("subject", ""),
            summary=row.get("summary", ""),
            evidence_count=int(str(row.get("evidence_count") or "0").strip() or 0) if str(row.get("evidence_count") or "").strip().isdigit() else 0,
        )
        subject, summary = _ticket_copy(tmp, finding)
        row["subject"] = subject
        row["summary"] = summary
        if abs(old_requested - new_requested) > 0.001 or abs(old_recovered - new_recovered) > 0.001:
            log.append(
                f"{row['request_id']}: requested {old_requested:.2f}->{new_requested:.2f} "
                f"recovered {old_recovered:.2f}->{new_recovered:.2f} "
                f"(finding {finding.finding_id} PR={finding.recoverable_amount_inr:.2f})"
            )
    _write_csv(path, fieldnames, rows)
    return log


def main() -> None:
    repo = DataRepository()
    repo.load()
    engine = FinancialEngine(repo)
    print("period,finding_id,type,old_csv_impact,engine_ma,engine_pr")
    for period in PERIODS:
        p_dir = DATA_ROOT / period
        findings = engine.get_findings(period=period)
        old_rows = list(csv.DictReader((p_dir / "anomalies.csv").open("r", encoding="utf-8")))
        old_by_id = {row["anomaly_id"]: row for row in old_rows}
        for finding in findings:
            old = old_by_id.get(finding.finding_id, {})
            print(
                f"{period},{finding.finding_id},{finding.type},"
                f"{old.get('financial_impact','')},{finding.financial_impact_inr:.2f},"
                f"{finding.recoverable_amount_inr:.2f}"
            )
        by_id = _sync_anomalies(p_dir, findings)
        _sync_evidence(p_dir, findings)
        logs = _sync_requests(p_dir, by_id, repo.get_recovery_requests(period=period))
        for line in logs:
            print("  TICKET", line)


if __name__ == "__main__":
    main()
