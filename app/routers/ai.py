"""AI-assisted endpoints for explaining simulation previews."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.models import User
from app.schemas.ai import (
    SimulationExplanationRequest,
    SimulationExplanationResponse,
)
from app.services.ai import (
    GroqNotConfiguredError,
    GroqServiceError,
    explain_simulation,
)
from app.services.simulation import preview_simulation
from app.schemas.simulation import SimulationPreviewRequest

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/status")
def ai_status(
    _current_user: User = Depends(get_current_user),
) -> dict[str, str | bool]:
    """Report configuration state without exposing credentials."""
    return {
        "provider": "groq",
        "configured": bool(settings.groq_api_key),
        "model": settings.groq_model,
    }


@router.post(
    "/simulation/explain",
    response_model=SimulationExplanationResponse,
)
def explain_preview(
    payload: SimulationExplanationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SimulationExplanationResponse:
    """Run the deterministic preview and ask Groq to explain its output."""
    preview_payload = SimulationPreviewRequest(
        route_ids=payload.route_ids,
        elapsed_s=payload.elapsed_s,
    )

    try:
        deterministic_result = preview_simulation(
            db,
            owner_id=current_user.id,
            payload=preview_payload,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    except Exception:
        # Do not disclose database or implementation details to API callers.
        raise HTTPException(
            status_code=404,
            detail="Route, aircraft or simulation resource not found",
        ) from None

    # The client may request an explanation of the preview but cannot replace
    # the backend-calculated positions, timing, or aircraft state.
    if payload.simulation_result:
        client_state_ids = {
            str(item.get("aircraft_id"))
            for item in payload.simulation_result.get("states", [])
            if isinstance(item, dict)
        }
        server_state_ids = {str(item.aircraft_id) for item in deterministic_result.states}
        if client_state_ids and client_state_ids != server_state_ids:
            raise HTTPException(
                status_code=422,
                detail="Simulation result does not match the selected routes",
            )

    result_data = deterministic_result.model_dump()
    request_data = {
        "route_ids": payload.route_ids,
        "elapsed_s": payload.elapsed_s,
    }

    try:
        explanation = explain_simulation(request_data, result_data)
    except GroqNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None
    except GroqServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from None

    return SimulationExplanationResponse(
        model=settings.groq_model,
        explanation=explanation,
    )
