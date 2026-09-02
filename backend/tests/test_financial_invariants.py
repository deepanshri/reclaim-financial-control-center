"""
Hard financial requirements that must hold for every audit period.

These tests prove Money Affected and Potential Recovery from source records,
not from summary.csv or frontend constants.
"""
from pathlib import Path

from tests.http import authenticated_client
from app.services.data_repository import DataRepository
from app.services.financial_engine import FinancialEngine

client = authenticated_client()

PERIODS = ["2024_H1", "2024_H2", "2025_H1", "2025_H2", "2026_H1", "2026_H2"]
H1_MONTHS = ["01", "02", "03", "04", "05", "06"]
H2_MONTHS = ["07", "08", "09", "10", "11", "12"]
DATA_ROOT = Path(__file__).resolve().parent.parent / "data" / "reclaim_six_half_year_datasets"


def _engine():
    repo = DataRepository()
    repo.load()
    return FinancialEngine(repo), repo


def test_six_periods_exist():
    engine, repo = _engine()
    periods = engine.get_available_periods()
    assert [p["key"] for p in periods] == ["2026_H2", "2026_H1", "2025_H2", "2025_H1", "2024_H2", "2024_H1"]
    for key in PERIODS:
        assert (DATA_ROOT / key).is_dir()
        assert repo.get_all_payments(period=key)


def test_every_period_has_exactly_six_report_months():
    engine, _ = _engine()
    for period in PERIODS:
        months = engine.get_monthly_reports(period=period)
        assert len(months) == 6, period
        year = period[:4]
        expected = [f"{year}-{m}" for m in (H1_MONTHS if period.endswith("H1") else H2_MONTHS)]
        assert [m["month"] for m in months] == expected


def test_payment_volume_is_calculated_from_source_transactions():
    engine, repo = _engine()
    for period in PERIODS:
        payments = repo.get_all_payments(period=period)
        source_volume = round(sum(p.amount_paise for p in payments) / 100.0, 2)
        status = engine.get_financial_status(period=period)
        assert status["total_payment_volume_inr"] == source_volume
        crore = source_volume / 1e7
        assert 40.0 <= crore <= 60.0, f"{period} volume {crore:.2f} Cr outside 40-60 Cr"


def test_refunds_reference_valid_payments_and_exist_in_every_period():
    _, repo = _engine()
    for period in PERIODS:
        payments = {p.id: p for p in repo.get_all_payments(period=period)}
        refunds = repo.get_all_refunds(period=period)
        assert len(refunds) > 0, f"{period} has no refunds"
        for refund in refunds:
            parent = payments.get(refund.payment_id)
            assert parent is not None, f"{refund.id} missing parent {refund.payment_id}"
            assert refund.amount_paise <= parent.amount_paise


def test_money_affected_reproducible_from_findings():
    engine, _ = _engine()
    for period in PERIODS:
        status = engine.get_financial_status(period=period)
        findings = [f for f in engine.get_findings(period=period) if f.status == "confirmed"]
        reproduced = round(sum(f.financial_impact_paise for f in findings) / 100.0, 2)
        assert status["money_affected_inr"] == reproduced
        assert status["confirmed_loss_inr"] == reproduced


def test_potential_recovery_is_independently_calculated():
    engine, _ = _engine()
    for period in PERIODS:
        status = engine.get_financial_status(period=period)
        findings = [f for f in engine.get_findings(period=period) if f.status == "confirmed"]
        reproduced = round(
            sum(
                f.recoverable_amount_paise
                for f in findings
                if f.is_recovery_eligible and f.recoverable_amount_paise > 0
            )
            / 100.0,
            2,
        )
        assert status["potential_recovery_inr"] == reproduced
        assert status["potential_loss_inr"] == reproduced
        # Independent: not a copy of money affected whenever confirmed findings exist
        if status["money_affected_inr"] > 0:
            assert status["potential_recovery_inr"] < status["money_affected_inr"], period


def test_recovery_inequalities():
    engine, _ = _engine()
    for period in PERIODS:
        status = engine.get_financial_status(period=period)
        ma = status["money_affected_inr"]
        pr = status["potential_recovery_inr"]
        requested = status["recovery_requested_inr"]
        recovered = status["recovered_inr"]
        under_review = status["under_review_inr"]
        not_recovered = status["not_recovered_inr"]
        assert pr <= ma + 0.001, period
        assert requested <= pr + 0.001, f"{period} requested {requested} > potential {pr}"
        assert recovered <= requested + 0.001, period
        assert abs((recovered + under_review + not_recovered) - requested) < 0.02, (
            f"{period} recovered {recovered} + under_review {under_review} + "
            f"not_recovered {not_recovered} != requested {requested}"
        )


def test_severity_matches_money_affected_thresholds():
    engine, _ = _engine()
    for period in PERIODS:
        status = engine.get_financial_status(period=period)
        ma = status["money_affected_inr"]
        if ma < 100000.0:
            assert status["severity_level"] == "healthy"
            assert status["severity_label"] == "MONITOR"
            assert status["is_action_required"] is False
        elif ma < 300000.0:
            assert status["severity_level"] == "needs_review"
            assert status["severity_label"] == "ACTION NEEDED"
            assert status["is_action_required"] is True
        else:
            assert status["severity_level"] == "action_needed"
            assert status["severity_label"] == "URGENT ACTION"
            assert status["is_action_required"] is True


def test_monthly_totals_reconcile_with_period_totals():
    engine, _ = _engine()
    for period in PERIODS:
        status = engine.get_financial_status(period=period)
        months = engine.get_monthly_reports(period=period)
        assert round(sum(m["gross_volume_inr"] for m in months), 2) == status["total_payment_volume_inr"]
        assert abs(sum(m["loss_detected_inr"] for m in months) - status["money_affected_inr"]) < 0.02


def test_api_financial_values_equal_backend_calculations():
    engine, _ = _engine()
    for period in PERIODS:
        calculated = engine.get_financial_status(period=period)
        response = client.get(f"/api/dashboard?period={period}")
        assert response.status_code == 200
        api = response.json()["financial_status"]
        for field in [
            "money_affected_inr",
            "potential_recovery_inr",
            "recovery_requested_inr",
            "recovered_inr",
            "under_review_inr",
            "not_recovered_inr",
            "health_score",
            "severity_level",
            "total_payment_volume_inr",
        ]:
            assert api[field] == calculated[field], f"{period} {field}"
        assert api["money_affected_inr"] != api["potential_recovery_inr"], period


def test_fee_overcharge_math_from_source_records():
    engine, repo = _engine()
    findings = engine.get_findings(period="2026_H2")
    fee = next(f for f in findings if f.type == "fee_rate_increase")
    payments = [
        p
        for p in repo.get_all_payments(period="2026_H2")
        if p.captured and (p.applied_fee_rate > 0.018 or p.anomaly_type == "fee_rate_increase")
    ]
    expected_fee = sum(round(p.amount_paise * 0.018) for p in payments)
    actual_fee = sum(p.fee_paise for p in payments)
    excess = actual_fee - expected_fee
    assert fee.financial_impact_paise == excess
    assert fee.recoverable_amount_paise == excess
    assert fee.recoverable_amount_paise == fee.financial_impact_paise


def test_duplicate_refund_excess_equals_second_debit():
    engine, repo = _engine()
    findings = engine.get_findings(period="2026_H2")
    dup = next(f for f in findings if f.type == "duplicate_refund")
    refunds = [r for r in repo.get_all_refunds(period="2026_H2") if r.anomaly_type == "duplicate_refund"]
    assert len(refunds) == 1
    assert dup.financial_impact_paise == refunds[0].amount_paise
    assert dup.recoverable_amount_paise == dup.financial_impact_paise


def test_missing_settlement_recovery_is_net_of_contracted_fee():
    engine, repo = _engine()
    findings = engine.get_findings(period="2026_H2")
    missing = next(f for f in findings if f.type == "missing_settlement")
    payments = [p for p in repo.get_all_payments(period="2026_H2") if p.anomaly_type == "missing_settlement"]
    assert len(payments) == 1
    payment = payments[0]
    assert missing.financial_impact_paise == payment.amount_paise
    contracted_fee = round(payment.amount_paise * 0.018)
    assert missing.recoverable_amount_paise == payment.amount_paise - contracted_fee
    assert missing.recoverable_amount_paise < missing.financial_impact_paise


def test_no_global_recovery_percent_multipliers():
    engine, _ = _engine()
    for period in PERIODS:
        for finding in engine.get_findings(period=period):
            if finding.status != "confirmed" or finding.financial_impact_paise <= 0:
                continue
            if not finding.is_recovery_eligible:
                assert finding.recoverable_amount_paise == 0
                continue
            ratio = finding.recoverable_amount_paise / finding.financial_impact_paise
            assert abs(ratio - 0.80) > 0.001
            assert abs(ratio - 0.85) > 0.001
            assert abs(ratio - 0.90) > 0.001
            assert abs(ratio - 0.95) > 0.001
            assert abs(ratio - 0.75) > 0.001
            assert abs(ratio - 0.70) > 0.001


def test_anomaly_evidence_matches_source_or_computed_difference():
    engine, repo = _engine()
    findings = engine.get_findings(period="2026_H2")
    fee = next(f for f in findings if f.type == "fee_rate_increase")
    assert len(fee.evidence) > 0
    for ev in fee.evidence:
        payment = repo.get_payment_by_id(ev.source_record_id, period="2026_H2")
        assert payment is not None
        expected_fee = round(payment.amount_paise * 0.018)
        assert ev.financial_impact_paise == payment.fee_paise - expected_fee

    missing = next(f for f in findings if f.type == "missing_settlement")
    payment = repo.get_payment_by_id(missing.source_record_ids[0], period="2026_H2")
    assert payment is not None
    assert missing.financial_impact_paise == payment.amount_paise


def test_recovery_request_outcomes_do_not_exceed_requested():
    engine, _ = _engine()
    for period in PERIODS:
        for req in engine.get_recovery_requests(period=period):
            assert req.amount_recovered_paise <= req.amount_requested_paise
            if req.status.lower() in ["under_review", "submitted", "pending", "rejected", "not_recovered", "failed"]:
                if req.status.lower() in ["rejected", "not_recovered", "failed"]:
                    assert req.amount_recovered_paise == 0


def test_periods_are_not_identical():
    engine, _ = _engine()
    volumes = [engine.get_financial_status(period=p)["total_payment_volume_inr"] for p in PERIODS]
    assert len(set(volumes)) == 6
    impacts = [engine.get_financial_status(period=p)["money_affected_inr"] for p in PERIODS]
    assert len(set(impacts)) == 6


def test_unknown_period_does_not_reuse_another_period_ledger():
    from app.core.exceptions import InvalidPeriodError

    _, repo = _engine()
    default_status_period = "2026_H2"
    default_volume = repo.get_all_payments(period=default_status_period)
    assert default_volume
    try:
        repo.normalize_period_key("2099_H1")
        raised = False
    except InvalidPeriodError:
        raised = True
    assert raised, "Unknown period must not silently resolve to another period"


def test_api_unknown_period_is_rejected():
    res = client.get("/api/dashboard?period=2099_H1")
    assert res.status_code == 400
    body = res.json()
    detail = body.get("detail") or body
    assert detail.get("code") == "invalid_period"


def test_no_authoritative_hardcoded_react_financials():
    src_root = Path(__file__).resolve().parent.parent.parent / "src"
    forbidden = ["69104.85", "51789.85", "₹51,789.85", "286875"]
    for path in src_root.rglob("*.ts*"):
        if "mockData.ts" in path.name or "_archived" in path.name:
            continue
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"{path} contains {token}"


def test_loaded_anomaly_csv_matches_engine_fee_impacts():
    engine, _ = _engine()
    stale = ["286875", "248625.00", "146625.00", "119850.00"]
    for period in PERIODS:
        findings = {f.finding_id: f for f in engine.get_findings(period=period)}
        path = DATA_ROOT / period / "anomalies.csv"
        text = path.read_text(encoding="utf-8")
        for token in stale:
            assert token not in text, f"{path} still has stale {token}"
        import csv

        with path.open("r", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                finding = findings.get(row["anomaly_id"])
                if finding is None:
                    continue
                csv_impact = round(float(row["financial_impact"]), 2)
                csv_recoverable = round(float(row["recoverable_amount"] or 0), 2)
                assert csv_impact == finding.financial_impact_inr, row["anomaly_id"]
                assert csv_recoverable == finding.recoverable_amount_inr, row["anomaly_id"]


def test_recovery_tickets_match_current_eligible_amounts():
    engine, _ = _engine()
    for period in PERIODS:
        findings = {f.finding_id: f for f in engine.get_findings(period=period)}
        status = engine.get_financial_status(period=period)
        for req in engine.get_recovery_requests(period=period):
            if req.finding_id == "period_combined":
                assert req.amount_recovered_paise <= req.amount_requested_paise
                continue
            finding = findings.get(req.finding_id)
            assert finding is not None, req.request_id
            assert req.amount_recovered_paise <= req.amount_requested_paise
            if finding.is_recovery_eligible:
                assert req.amount_requested_paise <= finding.recoverable_amount_paise + 1
            else:
                assert req.amount_requested_paise == 0
        assert status["recovery_requested_inr"] <= status["potential_recovery_inr"] + 0.001
        assert status["recovered_inr"] <= status["recovery_requested_inr"] + 0.001
        assert abs(
            status["recovered_inr"]
            + status["under_review_inr"]
            + status["not_recovered_inr"]
            - status["recovery_requested_inr"]
        ) < 0.02


def test_statement_matching_rate_from_settlement_recon():
    engine, repo = _engine()
    for period in PERIODS:
        _, _, summary = engine.get_statement_ledger(period=period, page=1, page_size=10)
        recon = [row for row in repo.get_all_settlement_recon(period=period) if row.type == "payment"]
        expected = (
            round(100.0 * sum(1 for row in recon if row.settled) / len(recon), 2) if recon else 100.0
        )
        assert summary["matching_rate_percent"] == expected
        assert summary["matching_rate_percent"] != 99.8 or expected == 99.8


def test_summary_csv_matches_engine():
    import csv

    engine, _ = _engine()
    for period in PERIODS:
        status = engine.get_financial_status(period=period)
        path = DATA_ROOT / period / "summary.csv"
        with path.open(encoding="utf-8") as handle:
            row = next(csv.DictReader(handle))
        assert abs(float(row["gross_payment_volume"]) - status["total_payment_volume_inr"]) < 0.02
        assert abs(float(row["confirmed_loss"]) - status["money_affected_inr"]) < 0.02
        assert abs(float(row["potential_recovery"]) - status["potential_recovery_inr"]) < 0.02
        assert abs(float(row["recovery_requested"]) - status["recovery_requested_inr"]) < 0.02
        assert abs(float(row["recovered"]) - status["recovered_inr"]) < 0.02
        assert row["status"] == status["severity_label"]
        if "not_recovered" in row:
            assert abs(float(row["not_recovered"]) - status["not_recovered_inr"]) < 0.02


def test_merchant_facing_severity_labels_only():
    engine, _ = _engine()
    allowed = {"MONITOR", "ACTION NEEDED", "URGENT ACTION"}
    for period in PERIODS:
        status = engine.get_financial_status(period=period)
        assert status["severity_label"] in allowed
        assert status["severity_label"] not in {
            "REVIEW",
            "Healthy",
            "Needs Review",
            "ACTION NEEDED — REVIEW",
            "ACTION NEEDED — URGENT",
        }


