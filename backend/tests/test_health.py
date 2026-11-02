from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "GitAuto AI"}


def test_versioned_api_status() -> None:
    response = TestClient(app).get("/api/v1/status")

    assert response.status_code == 200
    assert response.json()["application"] == "GitAuto AI"


def test_unknown_route_returns_json_error() -> None:
    response = TestClient(app).get("/api/v1/unknown")

    assert response.status_code == 404
