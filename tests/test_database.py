from collections.abc import Generator

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.database import database
from app.database.base import Base


def test_database_url_uses_postgresql_psycopg() -> None:
    url = make_url(settings.database_url)

    assert url.drivername == "postgresql+psycopg"


def test_database_dependency_closes_session(monkeypatch) -> None:
    class FakeSession:
        closed = False

        def close(self) -> None:
            self.closed = True

    session = FakeSession()
    monkeypatch.setattr(database, "SessionLocal", lambda: session)
    dependency: Generator = database.get_db()

    assert next(dependency) is session

    try:
        next(dependency)
    except StopIteration:
        pass

    assert session.closed


def test_alembic_can_load_migration_directory() -> None:
    config = Config("alembic.ini")
    scripts = ScriptDirectory.from_config(config)

    assert scripts.dir.endswith("/alembic")
    assert scripts.get_heads() == []


def test_declarative_base_is_available_for_models() -> None:
    assert Base.metadata.tables == {}
