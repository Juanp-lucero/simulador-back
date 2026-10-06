from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_returns_api_status() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"name": "AeroMind IA API", "status": "ok"}


def test_health_endpoint_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_docs_are_available() -> None:
    response = client.get("/docs")

    assert response.status_code == 200


def test_cors_allows_local_angular_origin() -> None:
    response = client.options(
        "/",
        headers={
            "Origin": "http://localhost:4200",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:4200"
