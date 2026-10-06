"""Aircraft owned by authenticated simulator users."""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, String,
    UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Aircraft(Base):
    __tablename__ = "aircraft"
    __table_args__ = (
        UniqueConstraint("registration", name="uq_aircraft_registration"),
        CheckConstraint("cruise_speed_mps > 0", name="ck_aircraft_speed_positive"),
        CheckConstraint("max_altitude_m > 0", name="ck_aircraft_altitude_positive"),
        Index("ix_aircraft_owner_id", "owner_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    registration: Mapped[str] = mapped_column(String(15), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    cruise_speed_mps: Mapped[float] = mapped_column(Float, nullable=False)
    max_altitude_m: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
