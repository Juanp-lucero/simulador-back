"""Registration, login, and current-user endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.security import SecurityConfigurationError, create_access_token
from app.database.database import get_db
from app.models import User
from app.schemas.auth import RegisterRequest, TokenResponse, UserResponse
from app.services.auth import (
    AccountAlreadyExistsError,
    authenticate_user,
    register_user,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a user",
)
def register(
    payload: RegisterRequest, db: Session = Depends(get_db)
) -> User:
    try:
        return register_user(db, payload)
    except AccountAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username already registered",
        ) from None


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Create an access token",
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = authenticate_user(db, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token = create_access_token(
            subject=str(user.id),
            email=user.email,
            role=user.role,
        )
    except SecurityConfigurationError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured",
        ) from None
    return TokenResponse(access_token=token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the authenticated user",
)
def read_current_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user
