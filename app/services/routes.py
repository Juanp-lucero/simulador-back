"""Owner-scoped route and waypoint operations."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.aircraft import Aircraft
from app.models.route import Route, RouteWaypoint
from app.schemas.operations import RouteWrite


class RouteAlreadyExistsError(ValueError):
    """A route with this name already exists for the user."""


class RouteNotFoundError(LookupError):
    """The route is not visible to this user."""


class RouteAircraftNotFoundError(LookupError):
    """The selected aircraft is not visible to this user."""


def list_routes(db: Session, *, owner_id: int, offset: int, limit: int) -> list[Route]:
    statement = (
        select(Route)
        .options(selectinload(Route.waypoints))
        .where(Route.owner_id == owner_id)
        .order_by(Route.id)
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(statement))


def get_route(db: Session, *, owner_id: int, route_id: int) -> Route:
    statement = (
        select(Route)
        .options(selectinload(Route.waypoints))
        .where(Route.id == route_id, Route.owner_id == owner_id)
    )
    route = db.scalar(statement)
    if route is None:
        raise RouteNotFoundError
    return route


def _validate_aircraft(
    db: Session, *, owner_id: int, aircraft_id: int | None
) -> None:
    if aircraft_id is None:
        return
    aircraft = db.scalar(
        select(Aircraft.id).where(
            Aircraft.id == aircraft_id,
            Aircraft.owner_id == owner_id,
        )
    )
    if aircraft is None:
        raise RouteAircraftNotFoundError


def _waypoints(payload: RouteWrite) -> list[RouteWaypoint]:
    return [
        RouteWaypoint(sequence=index, **waypoint.model_dump())
        for index, waypoint in enumerate(payload.waypoints, start=1)
    ]


def create_route(db: Session, *, owner_id: int, payload: RouteWrite) -> Route:
    _validate_aircraft(db, owner_id=owner_id, aircraft_id=payload.aircraft_id)
    route = Route(
        owner_id=owner_id,
        name=payload.name,
        aircraft_id=payload.aircraft_id,
        waypoints=_waypoints(payload),
    )
    db.add(route)
    try:
        db.commit()
        return get_route(db, owner_id=owner_id, route_id=route.id)
    except IntegrityError as exc:
        db.rollback()
        raise RouteAlreadyExistsError from exc


def update_route(
    db: Session, *, owner_id: int, route_id: int, payload: RouteWrite
) -> Route:
    route = get_route(db, owner_id=owner_id, route_id=route_id)
    _validate_aircraft(db, owner_id=owner_id, aircraft_id=payload.aircraft_id)
    route.name = payload.name
    route.aircraft_id = payload.aircraft_id
    try:
        # Delete old rows before inserting their replacements: otherwise the
        # (route_id, sequence) unique constraint can collide during ORM flush.
        route.waypoints.clear()
        db.flush()
        route.waypoints = _waypoints(payload)
        db.commit()
        return get_route(db, owner_id=owner_id, route_id=route_id)
    except IntegrityError as exc:
        db.rollback()
        raise RouteAlreadyExistsError from exc


def delete_route(db: Session, *, owner_id: int, route_id: int) -> None:
    route = get_route(db, owner_id=owner_id, route_id=route_id)
    db.delete(route)
    db.commit()
