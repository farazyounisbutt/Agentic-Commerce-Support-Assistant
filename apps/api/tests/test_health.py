from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_success() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200


def test_health_endpoint_returns_expected_structure() -> None:
    response = client.get("/api/health")

    assert response.json() == {
        "status": "ok",
        "service": "agentic-commerce-support-api",
    }

