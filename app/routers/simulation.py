"""Deterministic simulation preview and saved runs."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.models import User
from app.schemas.simulation import (
    SimulationPreviewRequest,
    SimulationPreviewResponse,
    SimulationRunCreate,
    SimulationRunResponse,
    SimulationRunSummary,
)
from app.services.aircraft import AircraftNotFoundError
from app.services.routes import RouteNotFoundError
from app.services.simulation import preview_simulation
from app.services import simulation_runs
from app.services.simulation_runs import SimulationRunNotFoundError

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


@router.post(
    "/runs",
    response_model=SimulationRunResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_run(
    payload: SimulationRunCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SimulationRunResponse:
    """Save a scenario with the deterministic result computed right now."""
    try:
        run = simulation_runs.create_run(db, owner_id=current_user.id, payload=payload)
    except (RouteNotFoundError, AircraftNotFoundError):
        raise HTTPException(status_code=404, detail="Route or aircraft not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    return simulation_runs.to_response(run)


@router.get("/runs", response_model=list[SimulationRunSummary])
def list_runs(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SimulationRunSummary]:
    runs = simulation_runs.list_runs(
        db, owner_id=current_user.id, offset=offset, limit=limit
    )
    return [simulation_runs.to_summary(run) for run in runs]


@router.get("/runs/{run_id}", response_model=SimulationRunResponse)
def get_run(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SimulationRunResponse:
    try:
        run = simulation_runs.get_run(db, owner_id=current_user.id, run_id=run_id)
    except SimulationRunNotFoundError:
        raise HTTPException(status_code=404, detail="Simulation run not found") from None
    return simulation_runs.to_response(run)


@router.delete("/runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_run(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        simulation_runs.delete_run(db, owner_id=current_user.id, run_id=run_id)
    except SimulationRunNotFoundError:
        raise HTTPException(status_code=404, detail="Simulation run not found") from None
