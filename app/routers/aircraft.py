"""Authenticated aircraft CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.models import User
from app.schemas.operations import AircraftResponse, AircraftWrite
from app.services.aircraft import (
    AircraftAlreadyExistsError,
    AircraftNotFoundError,
    create_aircraft,
    delete_aircraft,
    get_aircraft,
    list_aircraft,
    update_aircraft,
)

router = APIRouter(prefix="/aircraft", tags=["aircraft"])


@router.post("", response_model=AircraftResponse, status_code=status.HTTP_201_CREATED)
def create(
    payload: AircraftWrite,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AircraftResponse:
    try:
        return create_aircraft(db, owner_id=current_user.id, payload=payload)
    except AircraftAlreadyExistsError:
        raise HTTPException(status_code=409, detail="Aircraft registration already exists") from None


@router.get("", response_model=list[AircraftResponse])
def list_mine(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AircraftResponse]:
    return list_aircraft(db, owner_id=current_user.id, offset=offset, limit=limit)


@router.get("/{aircraft_id}", response_model=AircraftResponse)
def read(
    aircraft_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AircraftResponse:
    try:
        return get_aircraft(db, owner_id=current_user.id, aircraft_id=aircraft_id)
    except AircraftNotFoundError:
        raise HTTPException(status_code=404, detail="Aircraft not found") from None


@router.put("/{aircraft_id}", response_model=AircraftResponse)
def update(
    aircraft_id: int,
    payload: AircraftWrite,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AircraftResponse:
    try:
        return update_aircraft(
            db, owner_id=current_user.id, aircraft_id=aircraft_id, payload=payload
        )
    except AircraftNotFoundError:
        raise HTTPException(status_code=404, detail="Aircraft not found") from None
    except AircraftAlreadyExistsError:
        raise HTTPException(status_code=409, detail="Aircraft registration already exists") from None


@router.delete("/{aircraft_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    aircraft_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    try:
        delete_aircraft(db, owner_id=current_user.id, aircraft_id=aircraft_id)
    except AircraftNotFoundError:
        raise HTTPException(status_code=404, detail="Aircraft not found") from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)
