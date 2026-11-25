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
from app.schemas.simulation import SimulationPreviewRequest
from app.services.ai import (
    GroqNotConfiguredError,
    GroqServiceError,
    explain_simulation,
    review_route,
    review_route_with_rules,
)
from app.services.aircraft import AircraftNotFoundError
from app.services.routes import RouteNotFoundError
from app.services.route_insights import compute_route_insights
from app.schemas.insights import RouteInsightsResponse, RouteReviewResponse
from app.services.simulation import preview_simulation
from app.services import simulation_runs
from app.services.simulation_runs import SimulationRunNotFoundError

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
    except RouteNotFoundError:
        raise HTTPException(status_code=404, detail="Route not found") from None
    except AircraftNotFoundError:
        raise HTTPException(status_code=404, detail="Aircraft not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None

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


@router.post(
    "/simulation/runs/{run_id}/explain",
    response_model=SimulationExplanationResponse,
)
def explain_saved_run(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SimulationExplanationResponse:
    """Explain a saved run with AI and store the explanation with it."""
    try:
        run = simulation_runs.get_run(db, owner_id=current_user.id, run_id=run_id)
    except SimulationRunNotFoundError:
        raise HTTPException(status_code=404, detail="Simulation run not found") from None

    request_data = {
        "name": run.name,
        "route_ids": run.route_ids,
        "elapsed_s": run.elapsed_s,
    }
    try:
        explanation = explain_simulation(request_data, run.result)
    except GroqNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None
    except GroqServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from None

    simulation_runs.save_explanation(
        db, owner_id=current_user.id, run_id=run.id, explanation=explanation
    )
    return SimulationExplanationResponse(
        model=settings.groq_model,
        explanation=explanation,
    )


@router.post("/routes/{route_id}/review", response_model=RouteReviewResponse)
def review_route_plan(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RouteReviewResponse:
    """Review a route plan with AI, falling back to the automatic checks."""
    try:
        insights = compute_route_insights(db, owner_id=current_user.id, route_id=route_id)
    except (RouteNotFoundError, AircraftNotFoundError):
        raise HTTPException(status_code=404, detail="Route not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None

    data = insights.as_dict()
    try:
        review = review_route(data)
        source, model = "ai", settings.groq_model
    except (GroqNotConfiguredError, GroqServiceError):
        review = review_route_with_rules(data)
        source, model = "rules", None

    return RouteReviewResponse(
        source=source,
        model=model,
        insights=RouteInsightsResponse(**data),
        **review,
    )
