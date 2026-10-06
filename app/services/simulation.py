"""Translate owned route plans into pure simulation inputs."""

from dataclasses import asdict

from sqlalchemy.orm import Session

from app.schemas.simulation import AircraftStateResponse, SimulationPreviewRequest, SimulationPreviewResponse
from app.services.aircraft import get_aircraft
from app.services.routes import get_route
from app.simulation.engine import Waypoint, sample_path


def preview_simulation(
    db: Session, *, owner_id: int, payload: SimulationPreviewRequest
) -> SimulationPreviewResponse:
    states: list[AircraftStateResponse] = []
    aircraft_ids: set[int] = set()
    for route_id in payload.route_ids:
        route = get_route(db, owner_id=owner_id, route_id=route_id)
        if route.aircraft_id is None:
            raise ValueError("Every simulated route must have an aircraft assigned")
        if route.aircraft_id in aircraft_ids:
            raise ValueError("An aircraft cannot fly two routes in the same preview")
        aircraft = get_aircraft(db, owner_id=owner_id, aircraft_id=route.aircraft_id)
        if any(point.altitude_m > aircraft.max_altitude_m for point in route.waypoints):
            raise ValueError("Route altitude exceeds the assigned aircraft limit")
        aircraft_ids.add(aircraft.id)
        points = [
            Waypoint(point.latitude_deg, point.longitude_deg, point.altitude_m, point.speed_mps)
            for point in route.waypoints
        ]
        state = sample_path(points, payload.elapsed_s)
        states.append(
            AircraftStateResponse(
                aircraft_id=aircraft.id,
                registration=aircraft.registration,
                route_id=route.id,
                route_name=route.name,
                **asdict(state),
            )
        )
    return SimulationPreviewResponse(elapsed_s=payload.elapsed_s, states=states)
