"""Dashboard statistics are computed per user."""

from tests.test_operations import (
    create_actor,
    operations_context,  # noqa: F401 - pytest fixture
)
from tests.test_route_insights import create_route


def test_stats_start_at_zero(operations_context) -> None:  # noqa: F811
    client, session_factory = operations_context
    _, headers = create_actor(session_factory, "pilot@example.com")
    stats = client.get("/stats", headers=headers).json()
    assert stats == {
        "aircraft_count": 0,
        "route_count": 0,
        "routes_without_aircraft": 0,
        "simulation_run_count": 0,
        "explained_run_count": 0,
        "planned_distance_km": 0.0,
    }


def test_stats_count_the_user_resources(operations_context) -> None:  # noqa: F811
    client, session_factory = operations_context
    _, headers = create_actor(session_factory, "pilot@example.com")
    _, other = create_actor(session_factory, "other@example.com")

    route_id = create_route(client, headers)
    create_route(client, headers, aircraft=False, name="Sin aeronave")
    client.post(
        "/simulation/runs",
        headers=headers,
        json={"name": "Run", "route_ids": [route_id], "elapsed_s": 0},
    )

    stats = client.get("/stats", headers=headers).json()
    assert stats["aircraft_count"] == 1
    assert stats["route_count"] == 2
    assert stats["routes_without_aircraft"] == 1
    assert stats["simulation_run_count"] == 1
    assert stats["explained_run_count"] == 0
    assert stats["planned_distance_km"] > 400

    assert client.get("/stats", headers=other).json()["route_count"] == 0


def test_stats_require_authentication(operations_context) -> None:  # noqa: F811
    client, _ = operations_context
    assert client.get("/stats").status_code == 401
