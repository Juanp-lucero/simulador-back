from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.dependencies import get_db
from app.core.security import create_access_token
from app.database.base import Base
from app.main import app
from app.models import User

TEST_SECRET = "operations-test-secret-that-is-not-used-outside-tests"


@pytest.fixture
def operations_context(
    monkeypatch,
) -> Generator[tuple[TestClient, sessionmaker[Session]], None, None]:
    monkeypatch.setattr(settings, "secret_key", TEST_SECRET)
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(connection, _record) -> None:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    test_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db() -> Generator[Session, None, None]:
        db = test_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            yield client, test_session
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def create_actor(
    session_factory: sessionmaker[Session], email: str
) -> tuple[int, dict[str, str]]:
    username = email.split("@", maxsplit=1)[0]
    with session_factory() as db:
        user = User(
            username=username,
            email=email,
            hashed_password="test-hash-not-used-by-these-tests",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = user.id
    token = create_access_token(subject=str(user_id), email=email, role="user")
    return user_id, {"Authorization": f"Bearer {token}"}


def aircraft_payload(**updates: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "registration": "hk-1234",
        "model_name": "Cessna 172",
        "cruise_speed_mps": 60,
        "max_altitude_m": 4000,
    }
    payload.update(updates)
    return payload


def route_payload(**updates: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "name": "Bogota - Medellin",
        "waypoints": [
            {
                "latitude_deg": 4.7016,
                "longitude_deg": -74.1469,
                "altitude_m": 2500,
                "speed_mps": 60,
            },
            {
                "latitude_deg": 6.1645,
                "longitude_deg": -75.4231,
                "altitude_m": 3000,
                "speed_mps": 60,
            },
        ],
    }
    payload.update(updates)
    return payload


def test_aircraft_crud_and_owner_isolation(operations_context) -> None:
    client, session_factory = operations_context
    owner_id, owner_headers = create_actor(session_factory, "pilot@example.com")
    _, other_headers = create_actor(session_factory, "other@example.com")

    assert client.get("/aircraft").status_code == 401

    created = client.post("/aircraft", headers=owner_headers, json=aircraft_payload())
    assert created.status_code == 201
    aircraft = created.json()
    assert aircraft["registration"] == "HK-1234"
    assert "owner_id" not in aircraft
    aircraft_id = aircraft["id"]

    duplicate = client.post(
        "/aircraft",
        headers=other_headers,
        json=aircraft_payload(registration="HK-1234"),
    )
    assert duplicate.status_code == 409

    own_list = client.get("/aircraft", headers=owner_headers)
    assert [item["id"] for item in own_list.json()] == [aircraft_id]
    assert client.get("/aircraft", headers=other_headers).json() == []
    assert client.get(f"/aircraft/{aircraft_id}", headers=other_headers).status_code == 404

    updated = client.put(
        f"/aircraft/{aircraft_id}",
        headers=owner_headers,
        json=aircraft_payload(registration="HK-5678", model_name="Cessna 208"),
    )
    assert updated.status_code == 200
    assert updated.json()["registration"] == "HK-5678"
    assert updated.json()["model_name"] == "Cessna 208"

    assert client.delete(f"/aircraft/{aircraft_id}", headers=owner_headers).status_code == 204
    assert client.get(f"/aircraft/{aircraft_id}", headers=owner_headers).status_code == 404
    assert owner_id > 0


def test_routes_crud_waypoint_order_and_aircraft_reference(operations_context) -> None:
    client, session_factory = operations_context
    _, headers = create_actor(session_factory, "planner@example.com")
    aircraft = client.post(
        "/aircraft", headers=headers, json=aircraft_payload()
    ).json()
    payload = route_payload(aircraft_id=aircraft["id"])

    created = client.post("/routes", headers=headers, json=payload)
    assert created.status_code == 201
    route = created.json()
    route_id = route["id"]
    assert route["aircraft_id"] == aircraft["id"]
    assert [point["sequence"] for point in route["waypoints"]] == [1, 2]
    assert route["waypoints"][0]["latitude_deg"] == pytest.approx(4.7016)

    listed = client.get("/routes", headers=headers)
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [route_id]

    replacement = route_payload(
        name="Bogota - Cali",
        aircraft_id=None,
        waypoints=[
            {
                "latitude_deg": 4.7016,
                "longitude_deg": -74.1469,
                "altitude_m": 2500,
                "speed_mps": 55,
            },
            {
                "latitude_deg": 3.5432,
                "longitude_deg": -76.3816,
                "altitude_m": 2800,
                "speed_mps": 55,
            },
        ],
    )
    updated = client.put(f"/routes/{route_id}", headers=headers, json=replacement)
    assert updated.status_code == 200
    assert updated.json()["name"] == "Bogota - Cali"
    assert updated.json()["aircraft_id"] is None
    assert len(updated.json()["waypoints"]) == 2
    assert updated.json()["waypoints"][1]["longitude_deg"] == pytest.approx(-76.3816)

    assert client.delete(f"/routes/{route_id}", headers=headers).status_code == 204
    assert client.get(f"/routes/{route_id}", headers=headers).status_code == 404


def test_routes_reject_invalid_waypoints_and_foreign_aircraft(operations_context) -> None:
    client, session_factory = operations_context
    _, owner_headers = create_actor(session_factory, "owner@example.com")
    _, other_headers = create_actor(session_factory, "other-owner@example.com")
    aircraft = client.post(
        "/aircraft", headers=owner_headers, json=aircraft_payload()
    ).json()

    too_short = client.post(
        "/routes",
        headers=owner_headers,
        json=route_payload(waypoints=route_payload()["waypoints"][:1]),
    )
    assert too_short.status_code == 422

    invalid_coordinate = client.post(
        "/routes",
        headers=owner_headers,
        json=route_payload(
            waypoints=[
                {"latitude_deg": 95, "longitude_deg": 0, "altitude_m": 1000, "speed_mps": 50},
                {"latitude_deg": 0, "longitude_deg": 0, "altitude_m": 1000, "speed_mps": 50},
            ]
        ),
    )
    assert invalid_coordinate.status_code == 422

    foreign_aircraft = client.post(
        "/routes",
        headers=other_headers,
        json=route_payload(aircraft_id=aircraft["id"]),
    )
    assert foreign_aircraft.status_code == 404

    assert client.get(
        f"/aircraft/{aircraft['id']}", headers=other_headers
    ).status_code == 404


def test_route_name_is_unique_per_owner_and_aircraft_delete_unassigns(operations_context) -> None:
    client, session_factory = operations_context
    _, headers = create_actor(session_factory, "captain@example.com")
    aircraft = client.post(
        "/aircraft", headers=headers, json=aircraft_payload()
    ).json()
    payload = route_payload(aircraft_id=aircraft["id"])
    route = client.post("/routes", headers=headers, json=payload)
    assert route.status_code == 201

    duplicate = client.post("/routes", headers=headers, json=payload)
    assert duplicate.status_code == 409

    assert client.delete(
        f"/aircraft/{aircraft['id']}", headers=headers
    ).status_code == 204
    remaining_route = client.get(
        f"/routes/{route.json()['id']}", headers=headers
    )
    assert remaining_route.status_code == 200
    assert remaining_route.json()["aircraft_id"] is None
