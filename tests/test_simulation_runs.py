"""Saved simulation runs: persistence, ownership and validation."""

from tests.test_operations import (
    aircraft_payload,
    create_actor,
    operations_context,  # noqa: F401 - pytest fixture
    route_payload,
)


def create_route(client, headers) -> int:
    aircraft = client.post("/aircraft", headers=headers, json=aircraft_payload()).json()
    route = client.post(
        "/routes",
        headers=headers,
        json=route_payload(aircraft_id=aircraft["id"]),
    )
    assert route.status_code == 201, route.text
    return route.json()["id"]


def test_run_is_saved_with_its_result(operations_context) -> None:  # noqa: F811
    client, session_factory = operations_context
    _, headers = create_actor(session_factory, "pilot@example.com")
    route_id = create_route(client, headers)

    response = client.post(
        "/simulation/runs",
        headers=headers,
        json={"name": "  Vuelo   de prueba ", "route_ids": [route_id], "elapsed_s": 600},
    )
    assert response.status_code == 201, response.text
    run = response.json()
    assert run["name"] == "Vuelo de prueba"
    assert run["result"]["elapsed_s"] == 600
    assert run["result"]["states"][0]["route_id"] == route_id
    assert run["explanation"] is None

    listed = client.get("/simulation/runs", headers=headers).json()
    assert [item["id"] for item in listed] == [run["id"]]
    assert listed[0]["has_explanation"] is False

    detail = client.get(f"/simulation/runs/{run['id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["result"] == run["result"]


def test_runs_are_isolated_between_users(operations_context) -> None:  # noqa: F811
    client, session_factory = operations_context
    _, owner = create_actor(session_factory, "pilot@example.com")
    _, other = create_actor(session_factory, "other@example.com")
    route_id = create_route(client, owner)

    run = client.post(
        "/simulation/runs",
        headers=owner,
        json={"name": "Privado", "route_ids": [route_id], "elapsed_s": 0},
    ).json()

    assert client.get("/simulation/runs", headers=other).json() == []
    assert client.get(f"/simulation/runs/{run['id']}", headers=other).status_code == 404
    assert client.delete(f"/simulation/runs/{run['id']}", headers=other).status_code == 404
    assert client.post(
        "/simulation/runs",
        headers=other,
        json={"name": "Ajeno", "route_ids": [route_id], "elapsed_s": 0},
    ).status_code == 404


def test_run_can_be_deleted(operations_context) -> None:  # noqa: F811
    client, session_factory = operations_context
    _, headers = create_actor(session_factory, "pilot@example.com")
    route_id = create_route(client, headers)
    run = client.post(
        "/simulation/runs",
        headers=headers,
        json={"name": "Borrar", "route_ids": [route_id], "elapsed_s": 10},
    ).json()

    assert client.delete(f"/simulation/runs/{run['id']}", headers=headers).status_code == 204
    assert client.get(f"/simulation/runs/{run['id']}", headers=headers).status_code == 404


def test_invalid_runs_are_rejected(operations_context) -> None:  # noqa: F811
    client, session_factory = operations_context
    _, headers = create_actor(session_factory, "pilot@example.com")
    route_id = create_route(client, headers)

    blank = client.post(
        "/simulation/runs",
        headers=headers,
        json={"name": "   ", "route_ids": [route_id], "elapsed_s": 0},
    )
    assert blank.status_code == 422

    too_long = client.post(
        "/simulation/runs",
        headers=headers,
        json={"name": "Largo", "route_ids": [route_id], "elapsed_s": 90000},
    )
    assert too_long.status_code == 422

    assert client.get("/simulation/runs").status_code == 401


def test_run_can_be_renamed_only_by_its_owner(operations_context) -> None:  # noqa: F811
    client, session_factory = operations_context
    _, owner = create_actor(session_factory, "pilot@example.com")
    _, other = create_actor(session_factory, "other@example.com")
    route_id = create_route(client, owner)
    run = client.post(
        "/simulation/runs",
        headers=owner,
        json={"name": "Inicial", "route_ids": [route_id], "elapsed_s": 0},
    ).json()

    renamed = client.patch(
        f"/simulation/runs/{run['id']}", headers=owner, json={"name": "  Final  "}
    )
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "Final"
    assert client.patch(
        f"/simulation/runs/{run['id']}", headers=other, json={"name": "Robado"}
    ).status_code == 404


def test_runs_are_listed_newest_first_with_pagination(operations_context) -> None:  # noqa: F811
    client, session_factory = operations_context
    _, headers = create_actor(session_factory, "pilot@example.com")
    route_id = create_route(client, headers)
    ids = [
        client.post(
            "/simulation/runs",
            headers=headers,
            json={"name": f"Run {index}", "route_ids": [route_id], "elapsed_s": index},
        ).json()["id"]
        for index in range(3)
    ]

    listed = client.get("/simulation/runs", headers=headers).json()
    assert [item["id"] for item in listed] == list(reversed(ids))

    page = client.get("/simulation/runs?offset=1&limit=1", headers=headers).json()
    assert [item["id"] for item in page] == [ids[1]]
