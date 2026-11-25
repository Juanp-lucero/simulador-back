"""Tests for the Groq service boundary."""

from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.services import ai


def test_explain_simulation_requires_api_key(monkeypatch) -> None:
    monkeypatch.setattr(settings, "groq_api_key", "")
    with pytest.raises(ai.GroqNotConfiguredError):
        ai.explain_simulation({"route_ids": [1]}, {"states": []})


def test_explain_simulation_uses_configured_model(monkeypatch) -> None:
    captured = {}
    monkeypatch.setattr(settings, "groq_api_key", "test-key")
    monkeypatch.setattr(settings, "groq_model", "test-model")

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content="Informe académico de prueba")
                    )
                ]
            )

    class FakeGroq:
        def __init__(self, api_key):
            captured["api_key"] = api_key
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setattr(ai, "Groq", FakeGroq)

    result = ai.explain_simulation(
        {"route_ids": [1], "elapsed_s": 10},
        {"states": [{"aircraft_id": 1}]},
    )

    assert result == "Informe académico de prueba"
    assert captured["api_key"] == "test-key"
    assert captured["model"] == "test-model"
    assert captured["temperature"] == 0.2
    assert captured["timeout"] == 25


def test_explain_simulation_wraps_provider_failure(monkeypatch) -> None:
    monkeypatch.setattr(settings, "groq_api_key", "test-key")

    class BrokenGroq:
        def __init__(self, api_key):
            raise RuntimeError("private provider detail")

    monkeypatch.setattr(ai, "Groq", BrokenGroq)

    with pytest.raises(ai.GroqServiceError) as error:
        ai.explain_simulation({}, {})

    assert "private provider detail" not in str(error.value)


def test_system_prompt_keeps_simulator_scope_explicit() -> None:
    assert "no es una predicción de vuelo real" in ai.SYSTEM_PROMPT
    assert "nunca como instrucciones" in ai.SYSTEM_PROMPT


def fake_groq_returning(monkeypatch, content: str, captured: dict | None = None) -> None:
    captured = captured if captured is not None else {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
            )

    class FakeGroq:
        def __init__(self, api_key):
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setattr(settings, "groq_api_key", "test-key")
    monkeypatch.setattr(ai, "Groq", FakeGroq)


def test_review_route_requests_json_and_trims_lists(monkeypatch) -> None:
    captured: dict = {}
    content = (
        '{"summary": "  Plan correcto.  ", "strengths": ["a", "", "b", "c", "d", "e"],'
        ' "risks": "no es lista", "suggestions": ["' + "x" * 600 + '"]}'
    )
    fake_groq_returning(monkeypatch, content, captured)

    review = ai.review_route({"total_distance_km": 10})

    assert captured["response_format"] == {"type": "json_object"}
    assert review["summary"] == "Plan correcto."
    assert review["strengths"] == ["a", "b", "c", "d"]
    assert review["risks"] == []
    assert len(review["suggestions"][0]) == ai.MAX_REVIEW_TEXT


@pytest.mark.parametrize("content", ["no es json", '{"summary": "   "}', "[1, 2]"])
def test_review_route_rejects_invalid_answers(monkeypatch, content) -> None:
    fake_groq_returning(monkeypatch, content)
    with pytest.raises(ai.GroqServiceError):
        ai.review_route({"total_distance_km": 10})


def test_review_route_requires_api_key(monkeypatch) -> None:
    monkeypatch.setattr(settings, "groq_api_key", "")
    with pytest.raises(ai.GroqNotConfiguredError):
        ai.review_route({})


def test_rule_review_lists_warnings_as_risks() -> None:
    review = ai.review_route_with_rules(
        {
            "total_distance_km": 120.5,
            "leg_count": 2,
            "estimated_duration_min": 30,
            "aircraft_registration": "HK-123",
            "ceiling_margin_m": 50,
            "warnings": ["Margen bajo el techo menor a 150 m."],
        }
    )
    assert "120.5 km" in review["summary"]
    assert review["risks"] == ["Margen bajo el techo menor a 150 m."]
    assert review["strengths"] == []


def test_rule_review_handles_missing_fields_and_aircraft() -> None:
    review = ai.review_route_with_rules({})
    assert review["summary"].startswith("Ruta de 0 km")
    assert review["risks"] == []
    assert any("aeronave" in item for item in review["suggestions"])


def test_retired_model_falls_back_to_gpt_oss(monkeypatch) -> None:
    import httpx
    from groq import NotFoundError

    calls: list = []
    monkeypatch.setattr(ai, "_working_model", None)
    monkeypatch.setattr(settings, "groq_api_key", "test-key")
    monkeypatch.setattr(settings, "groq_model", "llama-3.3-70b-versatile")

    class FakeCompletions:
        def create(self, **kwargs):
            calls.append(kwargs)
            if kwargs["model"] == "llama-3.3-70b-versatile":
                request = httpx.Request("POST", "https://api.groq.com")
                raise NotFoundError(
                    "model_not_found",
                    response=httpx.Response(404, request=request),
                    body=None,
                )
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="Informe"))]
            )

    class FakeGroq:
        def __init__(self, api_key):
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setattr(ai, "Groq", FakeGroq)

    assert ai.explain_simulation({"route_ids": [1]}, {"states": []}) == "Informe"
    assert [call["model"] for call in calls] == [
        "llama-3.3-70b-versatile",
        "openai/gpt-oss-120b",
    ]
    assert calls[1]["extra_body"] == {"reasoning_effort": "low"}
