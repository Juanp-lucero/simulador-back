"""Authenticated flight-route CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.models import User
from app.schemas.operations import RouteResponse, RouteWrite
from app.services.routes import (
    RouteAircraftNotFoundError,
    RouteAlreadyExistsError,
    RouteNotFoundError,
    create_route,
    delete_route,
    get_route,
    list_routes,
    update_route,
)

router = APIRouter(prefix="/routes", tags=["routes"])


@router.post("", response_model=RouteResponse, status_code=status.HTTP_201_CREATED)
def create(
    payload: RouteWrite,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RouteResponse:
    try:
        return create_route(db, owner_id=current_user.id, payload=payload)
    except RouteAircraftNotFoundError:
        raise HTTPException(status_code=404, detail="Aircraft not found") from None
    except RouteAlreadyExistsError:
        raise HTTPException(status_code=409, detail="Route name already exists") from None


@router.get("", response_model=list[RouteResponse])
def list_mine(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RouteResponse]:
    return list_routes(db, owner_id=current_user.id, offset=offset, limit=limit)


@router.get("/{route_id}", response_model=RouteResponse)
def read(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RouteResponse:
    try:
        return get_route(db, owner_id=current_user.id, route_id=route_id)
    except RouteNotFoundError:
        raise HTTPException(status_code=404, detail="Route not found") from None


@router.put("/{route_id}", response_model=RouteResponse)
def update(
    route_id: int,
    payload: RouteWrite,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RouteResponse:
    try:
        return update_route(
            db, owner_id=current_user.id, route_id=route_id, payload=payload
        )
    except RouteNotFoundError:
        raise HTTPException(status_code=404, detail="Route not found") from None
    except RouteAircraftNotFoundError:
        raise HTTPException(status_code=404, detail="Aircraft not found") from None
    except RouteAlreadyExistsError:
        raise HTTPException(status_code=409, detail="Route name already exists") from None


@router.delete("/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    try:
        delete_route(db, owner_id=current_user.id, route_id=route_id)
    except RouteNotFoundError:
        raise HTTPException(status_code=404, detail="Route not found") from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)
