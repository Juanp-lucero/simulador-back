"""SQLAlchemy declarative base for application models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class inherited by database models."""
