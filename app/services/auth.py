"""Business logic for account registration and login."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models import User
from app.schemas.auth import RegisterRequest


class AccountAlreadyExistsError(ValueError):
    """The email address or username is already registered."""


def register_user(db: Session, payload: RegisterRequest) -> User:
    email = str(payload.email).strip().lower()
    username = (payload.username or email.split("@", maxsplit=1)[0]).strip().lower()
    if payload.username is None:
        username = username[:50]

    existing_user = db.scalar(
        select(User).where((User.email == email) | (User.username == username))
    )
    if existing_user is not None:
        raise AccountAlreadyExistsError

    user = User(
        username=username,
        email=email,
        hashed_password=get_password_hash(payload.password.get_secret_value()),
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        raise AccountAlreadyExistsError from exc
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    normalized_email = email.strip().lower()
    user = db.scalar(select(User).where(User.email == normalized_email))
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
