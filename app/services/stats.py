"""Per-user numbers for the dashboard."""

from dataclasses import asdict, dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.aircraft import Aircraft
from app.models.route import Route
from app.models.simulation_run import SimulationRun
from app.simulation.engine import Waypoint, validate_path


@dataclass
class DashboardStats:
    aircraft_count: int
    route_count: int
    routes_without_aircraft: int
    simulation_run_count: int
    explained_run_count: int
    planned_distance_km: float

    def as_dict(self) -> dict:
        return asdict(self)


def _count(db: Session, statement) -> int:
    return int(db.scalar(statement) or 0)


def dashboard_stats(db: Session, *, owner_id: int) -> DashboardStats:
    routes = list(
        db.scalars(
            select(Route)
            .options(selectinload(Route.waypoints))
            .where(Route.owner_id == owner_id)
        )
    )

    planned_m = 0.0
    for route in routes:
        points = [
            Waypoint(p.latitude_deg, p.longitude_deg, p.altitude_m, p.speed_mps)
            for p in route.waypoints
        ]
        try:
            planned_m += sum(validate_path(points))
        except ValueError:
            continue

    return DashboardStats(
        aircraft_count=_count(
            db, select(func.count()).select_from(Aircraft).where(Aircraft.owner_id == owner_id)
        ),
        route_count=len(routes),
        routes_without_aircraft=sum(1 for route in routes if route.aircraft_id is None),
        simulation_run_count=_count(
            db,
            select(func.count())
            .select_from(SimulationRun)
            .where(SimulationRun.owner_id == owner_id),
        ),
        explained_run_count=_count(
            db,
            select(func.count())
            .select_from(SimulationRun)
            .where(
                SimulationRun.owner_id == owner_id,
                SimulationRun.explanation.is_not(None),
            ),
        ),
        planned_distance_km=round(planned_m / 1000, 1),
    )
