"""Environment-backed settings for the initial API."""

from os import getenv


def _read_origins(value: str) -> list[str]:
    return [origin.strip() for origin in value.split(",") if origin.strip()]


class Settings:
    """Small settings object that avoids adding a settings dependency."""

    def __init__(self) -> None:
        self.app_name = getenv("APP_NAME", "AeroMind IA API")
        self.environment = getenv("ENVIRONMENT", "development")
        self.cors_origins = _read_origins(
            getenv("CORS_ORIGINS", "http://localhost:4200")
        )
        self.database_url = getenv(
            "DATABASE_URL",
            "postgresql+psycopg://aeromind:change-me@localhost:5432/aeromind",
        )


settings = Settings()
