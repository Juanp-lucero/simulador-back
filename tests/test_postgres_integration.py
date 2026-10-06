"""Opt-in integration test against a disposable, migrated PostgreSQL database."""

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database.database import SessionLocal, engine
from app.main import app
from app.models import User


@pytest.mark.skipif(
    os.getenv("RUN_POSTGRES_TESTS") != "1",
    reason="Requires an explicitly configured disposable PostgreSQL database",
)
def test_postgres_authenticated_plan_lifecycle() -> None:
    assert engine.dialect.name == "postgresql"
    suffix = uuid4().hex[:10]
    email = f"pg-test-{suffix}@example.com"
    password = "PostgresIntegrationTest123!"
    with TestClient(app) as client:
        try:
            registered = client.post("/auth/register", json={"email": email, "password": password})
            assert registered.status_code == 201
            login = client.post("/auth/login", data={"username": email, "password": password})
            assert login.status_code == 200
            headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
            aircraft = client.post("/aircraft", headers=headers, json={
                "registration": f"PG-{suffix.upper()}",
                "model_name": "Integration aircraft",
                "cruise_speed_mps": 100,
                "max_altitude_m": 5000,
            })
            assert aircraft.status_code == 201
            aircraft_id = aircraft.json()["id"]
            payload = {
                "name": f"PG route {suffix}", "aircraft_id": aircraft_id,
                "waypoints": [
                    {"latitude_deg": 0, "longitude_deg": 0, "altitude_m": 1000, "speed_mps": 100},
                    {"latitude_deg": 0, "longitude_deg": 1, "altitude_m": 2000, "speed_mps": 100},
                ],
            }
            route = client.post("/routes", headers=headers, json=payload)
            assert route.status_code == 201
            route_id = route.json()["id"]
            payload["waypoints"][1]["altitude_m"] = 1500
            updated = client.put(f"/routes/{route_id}", headers=headers, json=payload)
            assert updated.status_code == 200
            assert updated.json()["waypoints"][1]["altitude_m"] == 1500
            preview = client.post("/simulation/preview", headers=headers, json={"route_ids": [route_id], "elapsed_s": 30})
            assert preview.status_code == 200
            assert preview.json()["states"][0]["longitude_deg"] > 0
            assert client.delete(f"/aircraft/{aircraft_id}", headers=headers).status_code == 204
            remaining = client.get(f"/routes/{route_id}", headers=headers)
            assert remaining.json()["aircraft_id"] is None
            assert client.delete(f"/routes/{route_id}", headers=headers).status_code == 204
        finally:
            # Only remove the account created by this test; FK cascades remove
            # any test assets left behind after an assertion failure.
            with SessionLocal() as db:
                user = db.scalar(select(User).where(User.email == email))
                if user is not None:
                    db.delete(user)
                    db.commit()
