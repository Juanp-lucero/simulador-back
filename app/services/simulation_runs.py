"""Owner-scoped saved simulation runs."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.simulation_run import SimulationRun
from app.schemas.simulation import (
    SimulationPreviewRequest,
    SimulationRunCreate,
    SimulationRunResponse,
    SimulationRunSummary,
)
from app.services.simulation import preview_simulation


class SimulationRunNotFoundError(LookupError):
    """The saved run is not visible to this user."""


def create_run(
    db: Session, *, owner_id: int, payload: SimulationRunCreate
) -> SimulationRun:
    """Compute the deterministic preview and store it with the scenario."""
    preview = preview_simulation(
        db,
        owner_id=owner_id,
        payload=SimulationPreviewRequest(
            route_ids=payload.route_ids, elapsed_s=payload.elapsed_s
        ),
    )
    run = SimulationRun(
        owner_id=owner_id,
        name=payload.name,
        route_ids=list(payload.route_ids),
        elapsed_s=payload.elapsed_s,
        result=preview.model_dump(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def list_runs(
    db: Session, *, owner_id: int, offset: int = 0, limit: int = 50
) -> list[SimulationRun]:
    statement = (
        select(SimulationRun)
        .where(SimulationRun.owner_id == owner_id)
        .order_by(SimulationRun.created_at.desc(), SimulationRun.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(statement))


def get_run(db: Session, *, owner_id: int, run_id: int) -> SimulationRun:
    run = db.scalar(
        select(SimulationRun).where(
            SimulationRun.id == run_id, SimulationRun.owner_id == owner_id
        )
    )
    if run is None:
        raise SimulationRunNotFoundError(run_id)
    return run


def rename_run(db: Session, *, owner_id: int, run_id: int, name: str) -> SimulationRun:
    run = get_run(db, owner_id=owner_id, run_id=run_id)
    run.name = name
    db.commit()
    db.refresh(run)
    return run


def save_explanation(
    db: Session, *, owner_id: int, run_id: int, explanation: str
) -> SimulationRun:
    run = get_run(db, owner_id=owner_id, run_id=run_id)
    run.explanation = explanation
    db.commit()
    db.refresh(run)
    return run


def delete_run(db: Session, *, owner_id: int, run_id: int) -> None:
    run = get_run(db, owner_id=owner_id, run_id=run_id)
    db.delete(run)
    db.commit()


def to_summary(run: SimulationRun) -> SimulationRunSummary:
    return SimulationRunSummary(
        id=run.id,
        name=run.name,
        route_ids=run.route_ids,
        elapsed_s=run.elapsed_s,
        has_explanation=bool(run.explanation),
        created_at=run.created_at,
    )


def to_response(run: SimulationRun) -> SimulationRunResponse:
    return SimulationRunResponse(
        **to_summary(run).model_dump(),
        result=run.result,
        explanation=run.explanation,
    )
