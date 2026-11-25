"""Deterministic metrics and checks of a route plan.

These numbers come only from the route geometry and the assigned aircraft.
They are shown to the user and also given to the AI as verified facts.
"""

from dataclasses import asdict, dataclass, field

from sqlalchemy.orm import Session

from app.services.aircraft import get_aircraft
from app.services.routes import get_route
from app.simulation.engine import Waypoint, validate_path

# Vertical rate (m/s) above which a leg is flagged as steep for a light aircraft.
STEEP_CLIMB_MPS = 10.0
# Remaining altitude (m) below the aircraft ceiling that is considered tight.
TIGHT_CEILING_MARGIN_M = 150.0


@dataclass
class RouteInsights:
    route_id: int
    route_name: str
    aircraft_registration: str | None
    waypoint_count: int
    leg_count: int
    total_distance_km: float
    estimated_duration_min: float
    min_altitude_m: float
    max_altitude_m: float
    min_speed_mps: float
    max_speed_mps: float
    aircraft_ceiling_m: float | None
    ceiling_margin_m: float | None
    max_vertical_rate_mps: float
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)


def compute_route_insights(db: Session, *, owner_id: int, route_id: int) -> RouteInsights:
    route = get_route(db, owner_id=owner_id, route_id=route_id)
    points = [
        Waypoint(p.latitude_deg, p.longitude_deg, p.altitude_m, p.speed_mps)
        for p in route.waypoints
    ]
    distances = validate_path(points)
    durations = [
        distance / points[index].speed_mps for index, distance in enumerate(distances)
    ]
    vertical_rates = [
        abs(points[index + 1].altitude_m - points[index].altitude_m) / duration
        for index, duration in enumerate(durations)
        if duration > 0
    ]

    aircraft = None
    if route.aircraft_id is not None:
        aircraft = get_aircraft(db, owner_id=owner_id, aircraft_id=route.aircraft_id)

    altitudes = [point.altitude_m for point in points]
    speeds = [point.speed_mps for point in points]
    max_altitude = max(altitudes)
    ceiling = aircraft.max_altitude_m if aircraft else None
    margin = round(ceiling - max_altitude, 1) if ceiling is not None else None

    warnings: list[str] = []
    if aircraft is None:
        warnings.append("La ruta no tiene una aeronave asignada; no se puede simular.")
    else:
        if margin is not None and margin < 0:
            warnings.append(
                f"La altitud máxima ({max_altitude:.0f} m) supera el techo de la aeronave "
                f"({ceiling:.0f} m)."
            )
        elif margin is not None and margin < TIGHT_CEILING_MARGIN_M:
            warnings.append(
                f"La ruta vuela a menos de {TIGHT_CEILING_MARGIN_M:.0f} m del techo de la aeronave."
            )
        if max(speeds) > aircraft.cruise_speed_mps * 1.2:
            warnings.append(
                "Algún tramo supera en más de 20 % la velocidad de crucero de la aeronave."
            )
    if vertical_rates and max(vertical_rates) > STEEP_CLIMB_MPS:
        warnings.append(
            f"Hay un tramo con una tasa vertical mayor a {STEEP_CLIMB_MPS:.0f} m/s."
        )

    return RouteInsights(
        route_id=route.id,
        route_name=route.name,
        aircraft_registration=aircraft.registration if aircraft else None,
        waypoint_count=len(points),
        leg_count=len(distances),
        total_distance_km=round(sum(distances) / 1000, 2),
        estimated_duration_min=round(sum(durations) / 60, 1),
        min_altitude_m=min(altitudes),
        max_altitude_m=max_altitude,
        min_speed_mps=min(speeds),
        max_speed_mps=max(speeds),
        aircraft_ceiling_m=ceiling,
        ceiling_margin_m=margin,
        max_vertical_rate_mps=round(max(vertical_rates), 2) if vertical_rates else 0.0,
        warnings=warnings,
    )
