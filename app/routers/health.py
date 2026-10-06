"""Root and health endpoints for the initial API."""

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/", tags=["system"], summary="API status")
async def read_root() -> dict[str, str]:
    """Return a small status response without exposing environment details."""
    return {"name": settings.app_name, "status": "ok"}


@router.get("/health", tags=["system"], summary="Health check")
async def read_health() -> dict[str, str]:
    return {"status": "ok"}
