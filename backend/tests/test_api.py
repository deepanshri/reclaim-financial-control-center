from tests.http import authenticated_client

client = authenticated_client()


def test_dataset_periods_endpoint():
    response = client.get("/api/dataset/periods")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 6
    action_periods = [p["key"] for p in data if p["is_action_required"]]
    healthy_periods = [p["key"] for p in data if not p["is_action_required"]]
    assert sorted(action_periods) == ["2024_H2", "2025_H1", "2026_H1", "2026_H2"]
    assert sorted(healthy_periods) == ["2024_H1", "2025_H2"]


def test_dataset_status():
    response = client.get("/api/dataset/status?period=2026_H2")
    assert response.status_code == 200
    data = response.json()
    assert data["merchant_name"] == "Zenzo Commerce"
    assert data["payment_provider"] == "Razorpay"
    assert data["payment_record_count"] > 0
    assert data["confirmed_anomaly_count"] >= 5


def test_merchant_endpoint():
    response = client.get("/api/merchant")
    assert response.status_code == 200
    data = response.json()
    assert data["merchant_name"] == "Zenzo Commerce"
    assert data["merchant_id"] == "mid_demo_ZC771042"
    assert data["currency"] == "INR"
    assert data["contract"]["fee_rate"] == 0.018


def test_payments_endpoint():
    response = client.get("/api/payments?period=2026_H2&page=1&page_size=20")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert len(data["data"]) == 20


def test_payments_filter_period():
    response = client.get("/api/payments?period=2024_H1&page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    for p in data["data"]:
        assert str(p["created_year"]) == "2024"


def test_refunds_endpoint():
    response = client.get("/api/refunds?period=2026_H2&page=1&page_size=15")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0


def test_settlements_endpoint():
    response = client.get("/api/settlements?period=2026_H2&page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert len(data["data"]) == 10


def test_anomalies_endpoint_action_period():
    response = client.get("/api/anomalies?period=2026_H2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5
    fee_anom = next((a for a in data if a["type"] == "fee_rate_increase"), None)
    assert fee_anom is not None
    assert fee_anom["status"] == "confirmed"
    assert fee_anom["financial_impact"] > 100000.0


def test_anomalies_endpoint_healthy_period():
    response = client.get("/api/anomalies?period=2024_H1&status=confirmed")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["financial_impact"] > 0
    assert data[0]["type"] in ["settlement_amount_discrepancy", "uncredited_refund"]


def test_dashboard_endpoint():
    response = client.get("/api/dashboard?period=2026_H2")
    assert response.status_code == 200
    data = response.json()
    assert data["financial_status"]["is_action_required"] is True
    assert data["financial_status"]["confirmed_finding_count"] >= 5
    assert len(data["available_periods"]) == 6


def test_recovery_requests_endpoint():
    response = client.get("/api/recovery-requests?period=2026_H2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_openapi_docs_endpoint():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "paths" in data
    assert "/api/health" in data["paths"]
    assert "/api/dataset/status" in data["paths"]
    assert "/api/dataset/periods" in data["paths"]
