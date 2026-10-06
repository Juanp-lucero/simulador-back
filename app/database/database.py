"""PostgreSQL engine and request-scoped SQLAlchemy sessions."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    """Yield one database session and always close it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
