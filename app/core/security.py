"""Password hashing and JWT access-token helpers."""

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

_password_hash = PasswordHash.recommended()
_ALLOWED_ALGORITHMS = {"HS256", "HS384", "HS512"}


class SecurityConfigurationError(RuntimeError):
    """Raised when token signing is requested without a configured key."""


def _get_signing_key() -> str:
    if len(settings.secret_key.encode("utf-8")) < 32:
        raise SecurityConfigurationError("SECRET_KEY must be at least 32 bytes")
    if settings.algorithm not in _ALLOWED_ALGORITHMS:
        raise SecurityConfigurationError("ALGORITHM must be a supported HMAC algorithm")
    return settings.secret_key


def get_password_hash(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _password_hash.verify(plain_password, hashed_password)


def create_access_token(
    *, subject: str, email: str, role: str, expires_delta: timedelta | None = None
) -> str:
    signing_key = _get_signing_key()

    now = datetime.now(timezone.utc)
    expires_at = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    claims: dict[str, Any] = {
        "sub": subject,
        "email": email,
        "role": role,
        "iat": now,
        "exp": expires_at,
    }
    return jwt.encode(claims, signing_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    signing_key = _get_signing_key()

    return jwt.decode(
        token,
        signing_key,
        algorithms=[settings.algorithm],
        options={"require": ["exp", "iat", "sub"]},
    )
