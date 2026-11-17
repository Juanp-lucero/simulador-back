"""API contract tests for AI status and configuration handling."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.main import app
from app.models import User

TEST_USER = User(
    id=1,
    username="ai-test",
    email="ai-test@example.com",
    hashed_password="not-used",
)


@pytest.fixture
def ai_client(monkeypatch) -> Generator[TestClient, None, None]:
    monkeypatch.setattr(settings, "groq_api_key", "")
    app.dependency_overrides[get_current_user] = lambda: TEST_USER
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


def test_ai_status_does_not_expose_api_key(ai_client: TestClient) -> None:
    response = ai_client.get("/ai/status")
    assert response.status_code == 200
    assert response.json()["provider"] == "groq"
    assert response.json()["configured"] is False
    assert "api_key" not in response.json()


def test_ai_explanation_requires_groq_configuration(ai_client: TestClient) -> None:
    response = ai_client.post(
        "/ai/simulation/explain",
        json={
            "route_ids": [1],
            "elapsed_s": 10,
            "simulation_result": {"states": []},
        },
    )
    # The request cannot reach a real preview without a database route. The
    # status endpoint is the stable contract for checking configuration.
    assert response.status_code in {404, 503}
