from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

DEMO_MERCHANT = settings.demo_merchant_id
DEMO_PASSWORD = settings.demo_password


def authenticated_client() -> TestClient:
    client = TestClient(app)
    client.__enter__()
    response = client.post(
        "/api/auth/login",
        json={"merchant_id": DEMO_MERCHANT, "password": DEMO_PASSWORD},
    )
    assert response.status_code == 200, response.text
    token = response.json()["token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client
