"""Deterministic route metrics and checks."""

from tests.test_operations import (
    aircraft_payload,
    create_actor,
    operations_context,  # noqa: F401 - pytest fixture
    route_payload,
)


def create_route(client, headers, *, aircraft=True, **route_updates) -> int:
    payload = route_payload(**route_updates)
    if aircraft:
        created = client.post("/aircraft", headers=headers, json=aircraft_payload()).json()
        payload["aircraft_id"] = created["id"]
    response = client.post("/routes", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_insights_report_distance_duration_and_margin(operations_context) -> None:  # noqa: F811
    client, session_factory = operations_context
    _, headers = create_actor(session_factory, "pilot@example.com")
    route_id = create_route(client, headers)

    insights = client.get(f"/routes/{route_id}/insights", headers=headers).json()

    # Bogotá - Medellín is roughly 215 km in a straight line.
    assert 200 < insights["total_distance_km"] < 230
    assert insights["leg_count"] == 1
    assert insights["estimated_duration_min"] > 50
    assert insights["aircraft_ceiling_m"] == 4000
    assert insights["ceiling_margin_m"] == 1000
    assert insights["warnings"] == []


def test_insights_warn_about_missing_aircraft(operations_context) -> None:  # noqa: F811
    client, session_factory = operations_context
    _, headers = create_actor(session_factory, "pilot@example.com")
    route_id = create_route(client, headers, aircraft=False)

    insights = client.get(f"/routes/{route_id}/insights", headers=headers).json()
    assert insights["aircraft_registration"] is None
    assert any("no tiene una aeronave" in warning for warning in insights["warnings"])


def test_insights_warn_about_a_tight_ceiling(operations_context) -> None:  # noqa: F811
    client, session_factory = operations_context
    _, headers = create_actor(session_factory, "pilot@example.com")
    waypoints = route_payload()["waypoints"]
    waypoints[1]["altitude_m"] = 3950
    route_id = create_route(client, headers, waypoints=waypoints)

    insights = client.get(f"/routes/{route_id}/insights", headers=headers).json()
    assert insights["ceiling_margin_m"] == 50
    assert any("techo" in warning for warning in insights["warnings"])


def test_insights_of_other_users_are_hidden(operations_context) -> None:  # noqa: F811
    client, session_factory = operations_context
    _, owner = create_actor(session_factory, "pilot@example.com")
    _, other = create_actor(session_factory, "other@example.com")
    route_id = create_route(client, owner)

    assert client.get(f"/routes/{route_id}/insights", headers=other).status_code == 404
