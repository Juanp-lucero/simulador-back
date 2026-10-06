"""FastAPI application entry point."""

import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.routers.auth import router as auth_router
from app.routers.health import router as health_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    description="API inicial para el simulador AeroMind IA.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def handle_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Keep raw password values out of validation error responses."""
    safe_errors = []
    for error in exc.errors():
        safe_error = dict(error)
        location = error.get("loc", ())
        if any(part in {"password", "hashed_password"} for part in location):
            safe_error.pop("input", None)
        safe_errors.append(safe_error)
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder({"detail": safe_errors}),
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(
    request: Request, exc: Exception
) -> JSONResponse:
    """Log unexpected errors and return a response without internal details."""
    logger.exception("Unhandled error for %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )


app.include_router(health_router)
app.include_router(auth_router)
