"""Root and health endpoints for the initial API."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.database import get_db

router = APIRouter()


@router.get("/", tags=["system"], summary="API status")
async def read_root() -> dict[str, str]:
    """Return a small status response without exposing environment details."""
    return {"name": settings.app_name, "status": "ok"}


@router.get("/health", tags=["system"], summary="Health check")
async def read_health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/details", tags=["system"], summary="Dependency status")
def read_health_details(db: Session = Depends(get_db)) -> dict[str, str | bool]:
    """Check the database and report whether AI is configured (no secrets)."""
    try:
        db.execute(text("SELECT 1"))
        database = "connected"
    except Exception:
        database = "unavailable"
    return {
        "status": "ok" if database == "connected" else "degraded",
        "database": database,
        "ai_configured": bool(settings.groq_api_key),
    }
