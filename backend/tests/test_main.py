from fastapi.testclient import TestClient
from src.main import app


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200
    assert body["data"]["status"] == "ok"
