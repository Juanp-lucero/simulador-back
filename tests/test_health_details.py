from app.core.config import settings
from tests.test_operations import operations_context  # noqa: F401 - pytest fixture


def test_health_details_report_database_and_ai(operations_context, monkeypatch) -> None:  # noqa: F811
    client, _ = operations_context
    monkeypatch.setattr(settings, "groq_api_key", "")
    body = client.get("/health/details").json()
    assert body == {"status": "ok", "database": "connected", "ai_configured": False}


def test_health_details_never_expose_the_key(operations_context, monkeypatch) -> None:  # noqa: F811
    client, _ = operations_context
    monkeypatch.setattr(settings, "groq_api_key", "gsk-secret-value")
    response = client.get("/health/details")
    assert response.json()["ai_configured"] is True
    assert "gsk-secret-value" not in response.text
