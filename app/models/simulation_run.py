"""Saved simulation runs, so users can review previous scenarios."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class SimulationRun(Base):
    __tablename__ = "simulation_runs"
    __table_args__ = (
        CheckConstraint(
            "elapsed_s >= 0 AND elapsed_s <= 86400",
            name="ck_simulation_runs_elapsed_range",
        ),
        Index("ix_simulation_runs_owner_id", "owner_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    route_ids: Mapped[list[int]] = mapped_column(JSON, nullable=False)
    elapsed_s: Mapped[float] = mapped_column(Float, nullable=False)
    # Deterministic snapshot returned by the engine when the run was saved.
    result: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    # Optional AI explanation stored with the run.
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
