from collections.abc import Generator
from datetime import timedelta

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.dependencies import get_db
from app.core.security import create_access_token, verify_password
from app.database.base import Base
from app.main import app
from app.models import User

TEST_SECRET = "test-only-signing-key-that-is-not-used-outside-tests"


@pytest.fixture
def auth_context(monkeypatch) -> Generator[tuple[TestClient, sessionmaker[Session]], None, None]:
    monkeypatch.setattr(settings, "secret_key", TEST_SECRET)
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    test_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db() -> Generator[Session, None, None]:
        db = test_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client, test_session
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def register_payload(**updates: str) -> dict[str, str]:
    payload = {
        "email": "pilot@example.com",
        "password": "StrongPass123!",
    }
    payload.update(updates)
    return payload


def test_register_stores_hash_and_never_returns_password_fields(auth_context) -> None:
    client, session_factory = auth_context
    response = client.post("/auth/register", json=register_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "pilot@example.com"
    assert body["username"] == "pilot"
    assert "password" not in body
    assert "hashed_password" not in body

    with session_factory() as db:
        user = db.scalar(select(User).where(User.email == "pilot@example.com"))
        assert user is not None
        assert user.hashed_password != "StrongPass123!"
        assert user.hashed_password.startswith("$argon2id$")
        assert verify_password("StrongPass123!", user.hashed_password)


def test_duplicate_email_is_rejected(auth_context) -> None:
    client, _ = auth_context
    assert client.post("/auth/register", json=register_payload()).status_code == 201

    response = client.post("/auth/register", json=register_payload())

    assert response.status_code == 409


def test_password_must_meet_minimum_length(auth_context) -> None:
    client, _ = auth_context

    response = client.post(
        "/auth/register",
        json=register_payload(password="s3cr3t7"),
    )

    assert response.status_code == 422
    assert "s3cr3t7" not in response.text


def test_login_and_current_user(auth_context) -> None:
    client, _ = auth_context
    client.post("/auth/register", json=register_payload())

    login_response = client.post(
        "/auth/login",
        data={"username": "pilot@example.com", "password": "StrongPass123!"},
    )

    assert login_response.status_code == 200
    token_body = login_response.json()
    assert token_body["token_type"] == "bearer"
    assert "StrongPass123!" not in token_body["access_token"]
    claims = jwt.decode(
        token_body["access_token"],
        TEST_SECRET,
        algorithms=["HS256"],
    )
    assert set(claims).isdisjoint({"password", "hashed_password"})
    assert claims["sub"] == "1"
    assert claims["role"] == "user"

    current_response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token_body['access_token']}"},
    )

    assert current_response.status_code == 200
    assert current_response.json()["email"] == "pilot@example.com"


def test_login_rejects_incorrect_password(auth_context) -> None:
    client, _ = auth_context
    client.post("/auth/register", json=register_payload())

    response = client.post(
        "/auth/login",
        data={"username": "pilot@example.com", "password": "WrongPass123!"},
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_login_rejects_unknown_email(auth_context) -> None:
    client, _ = auth_context

    response = client.post(
        "/auth/login",
        data={"username": "unknown@example.com", "password": "StrongPass123!"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"
    assert "StrongPass123!" not in response.text


def test_protected_endpoint_rejects_missing_and_invalid_tokens(auth_context) -> None:
    client, _ = auth_context

    assert client.get("/auth/me").status_code == 401
    invalid = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer not-a-jwt"},
    )
    assert invalid.status_code == 401


def test_expired_token_is_rejected(auth_context) -> None:
    client, _ = auth_context
    client.post("/auth/register", json=register_payload())
    token = create_access_token(
        subject="1",
        email="pilot@example.com",
        role="user",
        expires_delta=timedelta(seconds=-1),
    )

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


def test_missing_signing_secret_fails_closed(auth_context, monkeypatch) -> None:
    client, _ = auth_context
    client.post("/auth/register", json=register_payload())
    monkeypatch.setattr(settings, "secret_key", "")

    response = client.post(
        "/auth/login",
        data={"username": "pilot@example.com", "password": "StrongPass123!"},
    )

    assert response.status_code == 503


def test_short_signing_secret_fails_closed(auth_context, monkeypatch) -> None:
    client, _ = auth_context
    client.post("/auth/register", json=register_payload())
    monkeypatch.setattr(settings, "secret_key", "short")

    response = client.post(
        "/auth/login",
        data={"username": "pilot@example.com", "password": "StrongPass123!"},
    )

    assert response.status_code == 503


def test_unapproved_jwt_algorithm_fails_closed(auth_context, monkeypatch) -> None:
    client, _ = auth_context
    client.post("/auth/register", json=register_payload())
    monkeypatch.setattr(settings, "algorithm", "none")

    response = client.post(
        "/auth/login",
        data={"username": "pilot@example.com", "password": "StrongPass123!"},
    )

    assert response.status_code == 503
