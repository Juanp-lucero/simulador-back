"""Dashboard statistics of the authenticated user."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.models import User
from app.services.stats import dashboard_stats

router = APIRouter(prefix="/stats", tags=["stats"])


class DashboardStatsResponse(BaseModel):
    aircraft_count: int
    route_count: int
    routes_without_aircraft: int
    simulation_run_count: int
    explained_run_count: int
    planned_distance_km: float


@router.get("", response_model=DashboardStatsResponse)
def read_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardStatsResponse:
    return DashboardStatsResponse(**dashboard_stats(db, owner_id=current_user.id).as_dict())
