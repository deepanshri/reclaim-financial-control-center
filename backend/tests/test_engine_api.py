from tests.http import authenticated_client

client = authenticated_client()


def test_api_dashboard_endpoint():
    response = client.get("/api/dashboard?period=2026_H2")
    assert response.status_code == 200
    data = response.json()

    assert "financial_status" in data
    assert "confirmed_findings" in data
    assert "under_review_findings" in data
    assert "available_periods" in data
    assert data["financial_status"]["total_payment_volume_inr"] > 0
    assert len(data["confirmed_findings"]) >= 5
    assert len(data["available_periods"]) == 6


def test_api_statement_endpoint():
    response = client.get("/api/statement?period=2026_H2&page=1&page_size=25")
    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert "summary" in data
    assert len(data["items"]) == 25
    assert data["total"] > 0
    assert data["summary"]["total_payments_inr"] > 0


def test_api_anomalies_and_evidence():
    response = client.get("/api/anomalies?period=2026_H2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5

    hero = next((f for f in data if f["type"] == "fee_rate_increase"), None)
    assert hero is not None
    assert hero["financial_impact"] > 100000.0
    assert hero["affected_transactions"] > 0

    # Test evidence sub-route
    ev_response = client.get(f"/api/anomalies/{hero['finding_id']}/evidence?period=2026_H2")
    assert ev_response.status_code == 200
    ev_data = ev_response.json()
    assert ev_data["finding_id"] == hero["finding_id"]
    assert len(ev_data["evidence"]) > 0


def test_api_recovery_requests_endpoints():
    response = client.get("/api/recovery-requests?period=2026_H2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2

    first_id = data[0]["request_id"]
    detail_response = client.get(f"/api/recovery-requests/{first_id}?period=2026_H2")
    assert detail_response.status_code == 200
    assert detail_response.json()["request_id"] == first_id


def test_api_reports_endpoint():
    response = client.get("/api/reports?period=2026_H2")
    assert response.status_code == 200
    data = response.json()

    assert "monthly_breakdown" in data
    assert len(data["monthly_breakdown"]) == 6
    assert data["total_gross_volume_inr"] > 0


def test_api_profile_endpoint():
    response = client.get("/api/profile")
    assert response.status_code == 200
    data = response.json()
    assert data["merchant_name"] == "Zenzo Commerce"
    assert data["merchant_id"] == "mid_demo_ZC771042"
