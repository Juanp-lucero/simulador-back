"""Owner-scoped aircraft operations."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.aircraft import Aircraft
from app.schemas.operations import AircraftWrite


class AircraftAlreadyExistsError(ValueError):
    """The registration is already in use."""


class AircraftNotFoundError(LookupError):
    """The aircraft is not visible to this user."""


def list_aircraft(db: Session, *, owner_id: int, offset: int, limit: int) -> list[Aircraft]:
    statement = (
        select(Aircraft)
        .where(Aircraft.owner_id == owner_id)
        .order_by(Aircraft.id)
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(statement))


def get_aircraft(db: Session, *, owner_id: int, aircraft_id: int) -> Aircraft:
    aircraft = db.scalar(
        select(Aircraft).where(
            Aircraft.id == aircraft_id,
            Aircraft.owner_id == owner_id,
        )
    )
    if aircraft is None:
        raise AircraftNotFoundError
    return aircraft


def create_aircraft(db: Session, *, owner_id: int, payload: AircraftWrite) -> Aircraft:
    aircraft = Aircraft(owner_id=owner_id, **payload.model_dump())
    db.add(aircraft)
    try:
        db.commit()
        db.refresh(aircraft)
    except IntegrityError as exc:
        db.rollback()
        raise AircraftAlreadyExistsError from exc
    return aircraft


def update_aircraft(
    db: Session, *, owner_id: int, aircraft_id: int, payload: AircraftWrite
) -> Aircraft:
    aircraft = get_aircraft(db, owner_id=owner_id, aircraft_id=aircraft_id)
    for field, value in payload.model_dump().items():
        setattr(aircraft, field, value)
    try:
        db.commit()
        db.refresh(aircraft)
    except IntegrityError as exc:
        db.rollback()
        raise AircraftAlreadyExistsError from exc
    return aircraft


def delete_aircraft(db: Session, *, owner_id: int, aircraft_id: int) -> None:
    aircraft = get_aircraft(db, owner_id=owner_id, aircraft_id=aircraft_id)
    db.delete(aircraft)
    db.commit()
