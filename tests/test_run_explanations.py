"""AI explanations of saved runs (Groq is replaced by a fake)."""

from app.core.config import settings
from app.routers import ai as ai_router
from tests.test_operations import (
    create_actor,
    operations_context,  # noqa: F401 - pytest fixture
)
from tests.test_simulation_runs import create_route


def save_run(client, headers) -> int:
    route_id = create_route(client, headers)
    return client.post(
        "/simulation/runs",
        headers=headers,
        json={"name": "Explicar", "route_ids": [route_id], "elapsed_s": 300},
    ).json()["id"]


def test_explanation_is_generated_and_stored(operations_context, monkeypatch) -> None:  # noqa: F811
    client, session_factory = operations_context
    _, headers = create_actor(session_factory, "pilot@example.com")
    run_id = save_run(client, headers)

    captured = {}

    def fake_explain(request_data, result):
        captured["request"] = request_data
        captured["result"] = result
        return "La aeronave avanza hacia el segundo punto de ruta."

    monkeypatch.setattr(settings, "groq_api_key", "fake-key")
    monkeypatch.setattr(ai_router, "explain_simulation", fake_explain)

    response = client.post(f"/ai/simulation/runs/{run_id}/explain", headers=headers)
    assert response.status_code == 200, response.text
    assert "segundo punto" in response.json()["explanation"]
    assert captured["request"]["name"] == "Explicar"
    assert captured["result"]["elapsed_s"] == 300

    stored = client.get(f"/simulation/runs/{run_id}", headers=headers).json()
    assert stored["explanation"] == "La aeronave avanza hacia el segundo punto de ruta."
    listed = client.get("/simulation/runs", headers=headers).json()
    assert listed[0]["has_explanation"] is True


def test_explanation_without_ai_returns_503(operations_context, monkeypatch) -> None:  # noqa: F811
    client, session_factory = operations_context
    _, headers = create_actor(session_factory, "pilot@example.com")
    run_id = save_run(client, headers)
    monkeypatch.setattr(settings, "groq_api_key", "")

    response = client.post(f"/ai/simulation/runs/{run_id}/explain", headers=headers)
    assert response.status_code == 503


def test_cannot_explain_runs_of_other_users(operations_context) -> None:  # noqa: F811
    client, session_factory = operations_context
    _, owner = create_actor(session_factory, "pilot@example.com")
    _, other = create_actor(session_factory, "other@example.com")
    run_id = save_run(client, owner)

    response = client.post(f"/ai/simulation/runs/{run_id}/explain", headers=other)
    assert response.status_code == 404
