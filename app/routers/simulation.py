"""Deterministic route preview endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.models import User
from app.schemas.simulation import SimulationPreviewRequest, SimulationPreviewResponse
from app.services.aircraft import AircraftNotFoundError
from app.services.routes import RouteNotFoundError
from app.services.simulation import preview_simulation

router = APIRouter(prefix="/simulation", tags=["simulation"])


@router.post("/preview", response_model=SimulationPreviewResponse)
def preview(
    payload: SimulationPreviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SimulationPreviewResponse:
    try:
        return preview_simulation(db, owner_id=current_user.id, payload=payload)
    except (RouteNotFoundError, AircraftNotFoundError):
        raise HTTPException(status_code=404, detail="Route or aircraft not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
