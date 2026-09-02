"""
Patch source records so anomalies are mathematically reproducible.

Does not regenerate payment volumes. Adds dedicated bank-credit-missing
settlements, restores omitted daily-batch credits, injects settlement
shortfalls, and documents holdback ineligibility.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "data" / "reclaim_six_half_year_datasets"

# Daily batches that currently have no bank credit because the generator
# reused their IDs as fake "missing credit" evidence. Restore credits, then
# attach dedicated small anomaly settlements whose amount equals the impact.
RESTORE_BATCH_CREDITS = [
    ("2025_H1", "set_2025_H1_00052"),
    ("2026_H2", "set_2026_H2_00038"),
    ("2026_H2", "set_2026_H2_00021"),
]

DEDICATED_MISSING_CREDITS = [
    # period, new_id, utr, date, amount_paise, ts, anomaly_type title key
    {
        "period": "2025_H1",
        "id": "set_2025_H1_bc_miss",
        "utr": "UTR2025H1BCMISS",
        "date": "2025-04-15",
        "amount_paise": 2245000,
        "created_at": 1744707600,
        "anomaly_type": "bank_credit_missing",
        "replace_evidence_id": "set_2025_H1_00052",
        "replace_utr": "UTR2025H100052",
        "ifsc": False,
    },
    {
        "period": "2026_H2",
        "id": "set_2026_H2_bc_ifsc",
        "utr": "UTR2026H2BCIFSC",
        "date": "2026-09-16",
        "amount_paise": 1850000,
        "created_at": 1789549200,
        "anomaly_type": "bank_credit_missing",
        "replace_evidence_id": "set_2026_H2_00038",
        "replace_utr": "UTR2026H200038",
        "ifsc": True,
    },
    {
        "period": "2026_H2",
        "id": "set_2026_H2_bc_miss",
        "utr": "UTR2026H2BCMISS",
        "date": "2026-08-09",
        "amount_paise": 3420000,
        "created_at": 1786246800,
        "anomaly_type": "bank_credit_missing",
        "replace_evidence_id": "set_2026_H2_00021",
        "replace_utr": "UTR2026H200021",
        "ifsc": False,
    },
    {
        "period": "2026_H1",
        "id": "set_2026_H1_bc_ifsc",
        "utr": "UTR2026H1BCIFSC",
        "date": "2026-03-18",
        "amount_paise": 1850000,
        "created_at": 1742288400,
        "anomaly_type": "bank_credit_missing",
        "replace_evidence_id": "",
        "replace_utr": "",
        "ifsc": True,
        "new_anomaly": True,
    },
]

SETTLEMENT_SHORTFALLS = [
    # period, settlement_id, shortfall_paise
    ("2024_H1", "set_2024_H1_00087", 1770000),
    ("2024_H2", "set_2024_H2_00068", 2025000),
    ("2025_H2", "set_2025_H2_00094", 3330000),
    ("2026_H2", "set_2026_H2_00087", 2170000),
]

HOLDBACK_ANOMALIES = {
    "anom_2024_H1_001": (
        "false",
        "0.00",
        "Shortfall is explained as a merchant chargeback/holdback, not a gateway payout error.",
    ),
    "anom_2024_H2_003": (
        "false",
        "0.00",
        "Shortfall is explained as merchant chargeback/holdback; not recoverable via Razorpay dispute.",
    ),
    "anom_2025_H2_001": (
        "false",
        "0.00",
        "Shortfall is explained as a merchant chargeback/holdback, not a gateway payout error.",
    ),
    "anom_2026_H2_006": (
        "false",
        "0.00",
        "Shortfall is explained as merchant-initiated chargeback holdbacks on the same batch.",
    ),
}


def _read_csv(path: Path) -> tuple[list[str], list[dict]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    return fields, rows


def _write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})


def _ensure_anomaly_type(fields: list[str], rows: list[dict]) -> list[str]:
    if "anomaly_type" not in fields:
        fields = fields + ["anomaly_type"]
    for row in rows:
        row.setdefault("anomaly_type", row.get("anomaly_type", ""))
    return fields


def patch_period_settlements(period: str) -> None:
    p_dir = ROOT / period
    s_path = p_dir / "settlements.csv"
    bc_path = p_dir / "bank_credits.csv"
    s_fields, settlements = _read_csv(s_path)
    bc_fields, credits = _read_csv(bc_path)
    s_fields = _ensure_anomaly_type(s_fields, settlements)

    by_id = {row["id"]: row for row in settlements}
    credit_by_sid = {row["settlement_id"]: row for row in credits}

    # Restore omitted daily-batch credits
    for p_key, sid in RESTORE_BATCH_CREDITS:
        if p_key != period:
            continue
        settl = by_id.get(sid)
        if not settl:
            continue
        if sid in credit_by_sid:
            continue
        max_idx = 0
        for row in credits:
            try:
                max_idx = max(max_idx, int(row["bank_credit_id"].rsplit("_", 1)[-1]))
            except ValueError:
                pass
        credits.append(
            {
                "bank_credit_id": f"bc_{period}_{max_idx + 1:05d}",
                "settlement_id": sid,
                "utr": settl.get("utr", ""),
                "credit_date": settl.get("settlement_date", ""),
                "amount": settl.get("amount", "0"),
                "currency": "INR",
                "bank_status": "credited",
                "reference": f"ICICI/{settl.get('utr', '')}",
            }
        )
        credit_by_sid[sid] = credits[-1]

    # Dedicated missing-credit settlements
    existing_ids = {row["id"] for row in settlements}
    for spec in DEDICATED_MISSING_CREDITS:
        if spec["period"] != period:
            continue
        if spec["id"] in existing_ids:
            continue
        settlements.append(
            {
                "id": spec["id"],
                "entity": "settlement",
                "amount": str(spec["amount_paise"]),
                "status": "processed",
                "fees": "0",
                "tax": "0",
                "utr": spec["utr"],
                "created_at": str(spec["created_at"]),
                "settlement_date": spec["date"],
                "transaction_count": "1",
                "refund_adjustment": "0.00",
                "anomaly_type": spec["anomaly_type"],
            }
        )
        existing_ids.add(spec["id"])

    # Inject settlement shortfalls into settlement + matching bank credit
    credit_by_sid = {row["settlement_id"]: row for row in credits}
    for p_key, sid, shortfall in SETTLEMENT_SHORTFALLS:
        if p_key != period:
            continue
        settl = by_id.get(sid) or next((r for r in settlements if r["id"] == sid), None)
        if not settl:
            print(f"  WARN: settlement {sid} not found for shortfall")
            continue
        current = int(settl["amount"])
        marker = settl.get("anomaly_type", "")
        if marker == "settlement_amount_discrepancy":
            continue
        settl["amount"] = str(max(0, current - shortfall))
        settl["anomaly_type"] = "settlement_amount_discrepancy"
        bc = credit_by_sid.get(sid)
        if bc:
            bc_amt = int(bc["amount"])
            bc["amount"] = str(max(0, bc_amt - shortfall))

    _write_csv(s_path, s_fields, settlements)
    _write_csv(bc_path, bc_fields, credits)


def patch_evidence_and_anomalies(period: str) -> None:
    p_dir = ROOT / period
    ev_path = p_dir / "anomaly_evidence.csv"
    an_path = p_dir / "anomalies.csv"
    ev_fields, evidence = _read_csv(ev_path)
    an_fields, anomalies = _read_csv(an_path)

    for spec in DEDICATED_MISSING_CREDITS:
        if spec["period"] != period or not spec.get("replace_evidence_id"):
            continue
        for row in evidence:
            if row.get("transaction_id") == spec["replace_evidence_id"]:
                row["transaction_id"] = spec["id"]
                row["reference_id"] = spec["utr"]
        for row in anomalies:
            row["root_cause"] = row.get("root_cause", "").replace(
                spec["replace_evidence_id"], spec["id"]
            ).replace(spec.get("replace_utr", ""), spec["utr"])
            row["verification_method_b"] = row.get("verification_method_b", "").replace(
                spec.get("replace_utr", ""), spec["utr"]
            )

    for aid, (eligible, recov, reason) in HOLDBACK_ANOMALIES.items():
        for row in anomalies:
            if row.get("anomaly_id") == aid:
                row["is_recovery_eligible"] = eligible
                row["recoverable_amount"] = recov
                row["recovery_ineligibility_reason"] = reason

    # 2026_H1 dedicated IFSC finding (needed so Action Needed period has PR < MA)
    if period == "2026_H1":
        existing_ids = {row.get("anomaly_id") for row in anomalies}
        if "anom_2026_H1_003" not in existing_ids:
            anomalies.append(
                {
                    "anomaly_id": "anom_2026_H1_003",
                    "type": "bank_credit_missing",
                    "status": "confirmed",
                    "title": "Settlement Returned — Bank IFSC Update",
                    "detected_date": "2026-03-20",
                    "start_date": "2026-03-18",
                    "end_date": "2026-03-20",
                    "affected_transactions": "1",
                    "expected_value": "INR 18,500.00",
                    "actual_value": "INR 0.00",
                    "financial_impact": "18500.00",
                    "is_recovery_eligible": "false",
                    "recoverable_amount": "0.00",
                    "recovery_ineligibility_reason": (
                        "Bank returned the credit due to IFSC/account-detail mismatch; "
                        "not recoverable via Razorpay dispute."
                    ),
                    "currency": "INR",
                    "root_cause": (
                        "Settlement set_2026_H1_bc_ifsc (UTR UTR2026H1BCIFSC) was returned "
                        "by ICICI Bank due to merchant account IFSC update; not credited."
                    ),
                    "evidence_type": "settlement",
                    "verification_method_a": "Razorpay ledger shows processed settlement = INR 18,500.00",
                    "verification_method_b": "ICICI Bank confirmed return due to IFSC mismatch",
                }
            )
            evidence.append(
                {
                    "evidence_id": "ev_2026_H1_bc_001",
                    "anomaly_id": "anom_2026_H1_003",
                    "transaction_id": "set_2026_H1_bc_ifsc",
                    "reference_id": "UTR2026H1BCIFSC",
                    "date": "2026-03-18",
                    "expected_value": "18500.00",
                    "actual_value": "0.00",
                    "difference": "18500.00",
                    "gross_amount": "18500.00",
                    "method": "NEFT/RTGS",
                    "evidence_note": "Bank trace confirmed operational return due to IFSC update.",
                }
            )

    _write_csv(ev_path, ev_fields, evidence)
    _write_csv(an_path, an_fields, anomalies)


def main() -> None:
    print(f"Patching source records in {ROOT}")
    for period in ["2024_H1", "2024_H2", "2025_H1", "2025_H2", "2026_H1", "2026_H2"]:
        print(f"  {period}")
        patch_period_settlements(period)
        patch_evidence_and_anomalies(period)
    print("Done.")


if __name__ == "__main__":
    main()
