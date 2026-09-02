"""Lookup reference anomaly rows so detectors reuse stable finding IDs."""

from typing import Any, Dict, List, Optional, Tuple

from app.services.data_repository import DataRepository


def _as_bool(value: Any) -> bool:
    return str(value or "").strip().lower() in ("true", "1", "yes")


def reference_rows_by_type(repo: DataRepository, period: Optional[str], anom_type: str) -> List[Dict[str, Any]]:
    return [row for row in repo.get_reference_anomalies(period=period) if row.get("type") == anom_type]


def reference_row_for_source(
    repo: DataRepository,
    period: Optional[str],
    anom_type: str,
    source_record_id: str = "",
) -> Optional[Dict[str, Any]]:
    rows = reference_rows_by_type(repo, period, anom_type)
    if source_record_id:
        for ev in repo.get_reference_evidence(period=period):
            if ev.get("transaction_id") == source_record_id:
                aid = ev.get("anomaly_id")
                for row in rows:
                    if row.get("anomaly_id") == aid:
                        return row
    if len(rows) == 1:
        return rows[0]
    return rows[0] if rows else None


def finding_id_for(
    repo: DataRepository,
    period: Optional[str],
    anom_type: str,
    default_id: str,
    source_record_id: str = "",
) -> Tuple[str, Optional[Dict[str, Any]]]:
    row = reference_row_for_source(repo, period, anom_type, source_record_id)
    if row and row.get("anomaly_id"):
        return str(row["anomaly_id"]), row
    return default_id, row


def is_ifsc_return(row: Optional[Dict[str, Any]], title: str = "", reason: str = "") -> bool:
    blob = " ".join(
        [
            str((row or {}).get("title", "")),
            str((row or {}).get("root_cause", "")),
            str((row or {}).get("recovery_ineligibility_reason", "")),
            title,
            reason,
        ]
    ).lower()
    return "ifsc" in blob or "account-detail" in blob or "account detail" in blob


def is_explained_holdback(row: Optional[Dict[str, Any]]) -> bool:
    if not row:
        return False
    if not _as_bool(row.get("is_recovery_eligible", "true")):
        reason = str(row.get("recovery_ineligibility_reason", "")).lower()
        root = str(row.get("root_cause", "")).lower()
        if "holdback" in reason or "chargeback" in reason or "holdback" in root or "chargeback" in root:
            return True
        return False
    blob = " ".join(
        [
            str(row.get("recovery_ineligibility_reason", "")),
            str(row.get("root_cause", "")),
            str(row.get("title", "")),
        ]
    ).lower()
    return "holdback" in blob or "chargeback" in blob
