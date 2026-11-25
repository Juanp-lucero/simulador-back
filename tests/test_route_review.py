"""AI route review with a fake provider and the rule-based fallback."""

from app.core.config import settings
from app.routers import ai as ai_router
from app.services.ai import GroqServiceError
from tests.test_operations import (
    create_actor,
    operations_context,  # noqa: F401 - pytest fixture
)
from tests.test_route_insights import create_route


def test_review_uses_ai_when_available(operations_context, monkeypatch) -> None:  # noqa: F811
    client, session_factory = operations_context
    _, headers = create_actor(session_factory, "pilot@example.com")
    route_id = create_route(client, headers)

    received = {}

    def fake_review(insights):
        received.update(insights)
        return {
            "summary": "Plan coherente para una aeronave ligera.",
            "strengths": ["Margen amplio bajo el techo."],
            "risks": [],
            "suggestions": ["Agregar un punto intermedio."],
        }

    monkeypatch.setattr(settings, "groq_api_key", "fake-key")
    monkeypatch.setattr(ai_router, "review_route", fake_review)

    response = client.post(f"/ai/routes/{route_id}/review", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["source"] == "ai"
    assert body["summary"] == "Plan coherente para una aeronave ligera."
    assert body["insights"]["route_id"] == route_id
    # The AI receives the verified metrics, not raw user text only.
    assert received["total_distance_km"] == body["insights"]["total_distance_km"]


def test_review_falls_back_to_rules_without_ai(operations_context, monkeypatch) -> None:  # noqa: F811
    client, session_factory = operations_context
    _, headers = create_actor(session_factory, "pilot@example.com")
    route_id = create_route(client, headers, aircraft=False)
    monkeypatch.setattr(settings, "groq_api_key", "")

    body = client.post(f"/ai/routes/{route_id}/review", headers=headers).json()
    assert body["source"] == "rules"
    assert body["model"] is None
    assert any("aeronave" in risk for risk in body["risks"])


def test_review_falls_back_when_the_provider_fails(operations_context, monkeypatch) -> None:  # noqa: F811
    client, session_factory = operations_context
    _, headers = create_actor(session_factory, "pilot@example.com")
    route_id = create_route(client, headers)

    def failing_review(_insights):
        raise GroqServiceError("timeout")

    monkeypatch.setattr(ai_router, "review_route", failing_review)
    body = client.post(f"/ai/routes/{route_id}/review", headers=headers).json()
    assert body["source"] == "rules"
    assert "km" in body["summary"]


def test_review_of_other_users_routes_is_hidden(operations_context) -> None:  # noqa: F811
    client, session_factory = operations_context
    _, owner = create_actor(session_factory, "pilot@example.com")
    _, other = create_actor(session_factory, "other@example.com")
    route_id = create_route(client, owner)
    assert client.post(f"/ai/routes/{route_id}/review", headers=other).status_code == 404
