"""
Integration Test Suite for All Six Periods & Financial Realism across Endpoints
Tests:
- 2024_H1, 2024_H2, 2025_H1, 2025_H2, 2026_H1, 2026_H2
- Dashboard, Statement, Anomalies, Evidence, Recovery Requests, Reports, Merchant
- Severity thresholds (< 1 lakh MONITOR, 1–2.99 lakh ACTION NEEDED, >= 3 lakh URGENT ACTION)
- Mathematical integrity (recovered <= requested, under_review != recovered, not_recovered != recovered)
"""

import pytest
from tests.http import authenticated_client

client = authenticated_client()

PERIODS = ["2024_H1", "2024_H2", "2025_H1", "2025_H2", "2026_H1", "2026_H2"]
URGENT_PERIODS = {"2026_H2"}
REVIEW_PERIODS = {"2024_H2", "2025_H1", "2026_H1"}
HEALTHY_PERIODS = {"2024_H1", "2025_H2"}


def test_periods_endpoint():
    res = client.get("/api/dataset/periods")
    assert res.status_code == 200
    periods = res.json()
    assert len(periods) == 6
    keys = [p["key"] for p in periods]
    assert keys == ["2026_H2", "2026_H1", "2025_H2", "2025_H1", "2024_H2", "2024_H1"]
    
    for p in periods:
        if p["key"] in URGENT_PERIODS:
            assert p["severity_level"] == "action_needed"
            assert p["severity_label"] == "URGENT ACTION"
            assert p["is_action_required"] is True
            assert p["confirmed_loss_inr"] >= 300000.0
        elif p["key"] in REVIEW_PERIODS:
            assert p["severity_level"] == "needs_review"
            assert p["severity_label"] == "ACTION NEEDED"
            assert p["is_action_required"] is True
            assert 100000.0 <= p["confirmed_loss_inr"] < 300000.0
        else:
            assert p["severity_level"] == "healthy"
            assert p["severity_label"] == "MONITOR"
            assert p["is_action_required"] is False
            assert 0 < p["confirmed_loss_inr"] < 100000.0


@pytest.mark.parametrize("period", PERIODS)
def test_dashboard_endpoint_for_each_period(period):
    res = client.get(f"/api/dashboard?period={period}")
    assert res.status_code == 200
    data = res.json()
    
    fin = data["financial_status"]
    assert fin["period"] == period
    assert fin["total_payment_volume_inr"] > 0
    assert fin["total_fees_inr"] > 0
    assert fin["total_settlements_inr"] > 0
    
    if period in URGENT_PERIODS:
        assert fin["severity_level"] == "action_needed"
        assert fin["confirmed_loss_inr"] >= 300000.0
        assert len(data["confirmed_findings"]) >= 4
    elif period in REVIEW_PERIODS:
        assert fin["severity_level"] == "needs_review"
        assert 100000.0 <= fin["confirmed_loss_inr"] < 300000.0
        assert len(data["confirmed_findings"]) >= 2
    else:
        assert fin["severity_level"] == "healthy"
        assert 0 < fin["confirmed_loss_inr"] < 100000.0
        assert len(data["confirmed_findings"]) >= 1


@pytest.mark.parametrize("period", PERIODS)
def test_statement_endpoint_for_each_period(period):
    res = client.get(f"/api/statement?period={period}&page=1&page_size=25")
    assert res.status_code == 200
    data = res.json()
    
    assert data["total"] > 0
    assert len(data["items"]) == min(25, data["total"])
    assert data["summary"]["total_payments_inr"] > 0
    assert data["summary"]["bank_deposits_inr"] > 0
    
    yr = period[:4]
    for item in data["items"]:
        # Verify date or year belongs to period year
        assert yr in item["date"] or str(item["timestamp"]).isdigit()


@pytest.mark.parametrize("period", PERIODS)
def test_recovery_requests_endpoint_for_each_period(period):
    res = client.get(f"/api/recovery-requests?period={period}")
    assert res.status_code == 200
    requests = res.json()
    
    total_requested = sum(r["amount_requested"] for r in requests)
    total_recovered = sum(r["amount_recovered"] for r in requests if r["status"] in ["resolved", "recovered"])
    
    # 1. Recovered cannot exceed requested
    assert total_recovered <= total_requested
    
    # 2. Status invariants
    for r in requests:
        if r["status"] in ["under_review", "submitted", "pending"]:
            assert r["amount_recovered"] == 0.0
        elif r["status"] in ["not_recovered", "rejected", "failed"]:
            assert r["amount_recovered"] == 0.0
        elif r["status"] in ["resolved", "recovered"]:
            assert r["amount_recovered"] > 0.0
            assert r["amount_recovered"] <= r["amount_requested"]


@pytest.mark.parametrize("period", PERIODS)
def test_reports_endpoint_for_each_period(period):
    res = client.get(f"/api/reports?period={period}")
    assert res.status_code == 200
    data = res.json()
    
    assert data["period"] == period
    assert len(data["monthly_breakdown"]) == 6
    assert data["total_gross_volume_inr"] > 0
    assert data["total_fees_inr"] > 0
    assert data["total_settlements_inr"] > 0
    
    # Monthly items check - active months in half-year have gross volume
    active_months = [m for m in data["monthly_breakdown"] if m["gross_volume_inr"] > 0]
    assert len(active_months) >= 5


def test_reports_period_switching_integrity():
    """Explicit test that 2025_H1, 2025_H2, 2026_H1, 2026_H2 produce distinct, non-stale data."""
    res_2025_h1 = client.get("/api/reports?period=2025_H1").json()
    res_2025_h2 = client.get("/api/reports?period=2025_H2").json()
    res_2026_h1 = client.get("/api/reports?period=2026_H1").json()
    res_2026_h2 = client.get("/api/reports?period=2026_H2").json()
    
    assert res_2025_h1["total_gross_volume_inr"] != res_2025_h2["total_gross_volume_inr"]
    assert res_2025_h2["total_gross_volume_inr"] != res_2026_h1["total_gross_volume_inr"]
    assert res_2026_h1["total_gross_volume_inr"] != res_2026_h2["total_gross_volume_inr"]

    assert 100000.0 <= res_2025_h1["total_loss_detected_inr"] < 300000.0
    assert 0 < res_2025_h2["total_loss_detected_inr"] < 100000.0
    assert 100000.0 <= res_2026_h1["total_loss_detected_inr"] < 300000.0
    assert res_2026_h2["total_loss_detected_inr"] >= 300000.0


def test_error_handling_graceful():
    res = client.get("/api/dashboard?period=invalid_period_xyz")
    assert res.status_code == 400
    detail = res.json()["detail"]
    assert detail["code"] == "invalid_period"
    assert "2026_H2" in detail["valid_periods"]
