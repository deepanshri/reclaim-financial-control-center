from fastapi.testclient import TestClient

from app.main import app
from tests.http import DEMO_MERCHANT, DEMO_PASSWORD, authenticated_client


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["dataset_status"] in ("loaded", "not_loaded")
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"


def test_root_endpoint():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert data["health"] == "/api/health"


def test_dashboard_requires_auth():
    client = TestClient(app)
    response = client.get("/api/dashboard")
    assert response.status_code == 401
