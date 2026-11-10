"""Environment-backed settings for the AeroMind API."""

import os
from pathlib import Path


def _load_env_file() -> None:
    """Load variables from the backend .env file."""
    env_path = Path(__file__).resolve().parents[2] / ".env"

    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key and value and not os.environ.get(key):
            os.environ[key] = value


def _read_origins(value: str) -> list[str]:
    return [origin.strip() for origin in value.split(",") if origin.strip()]


_load_env_file()


class Settings:
    """Application settings."""

    def __init__(self) -> None:
        self.app_name = os.getenv("APP_NAME", "AeroMind IA API")
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.cors_origins = _read_origins(
            os.getenv("CORS_ORIGINS", "http://localhost:4200")
        )
        self.database_url = os.getenv("DATABASE_URL", "")
        self.secret_key = os.getenv("SECRET_KEY", "")
        self.algorithm = os.getenv("ALGORITHM", "HS256")
        self.access_token_expire_minutes = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        )


settings = Settings()
