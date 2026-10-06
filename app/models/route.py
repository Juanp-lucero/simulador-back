"""Flight routes and their ordered waypoints."""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

class Route(Base):
    __tablename__ = "routes"
    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_routes_owner_name"),
        Index("ix_routes_owner_id", "owner_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    aircraft_id: Mapped[int | None] = mapped_column(
        ForeignKey("aircraft.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    waypoints: Mapped[list["RouteWaypoint"]] = relationship(
        back_populates="route",
        cascade="all, delete-orphan",
        order_by="RouteWaypoint.sequence",
    )


class RouteWaypoint(Base):
    __tablename__ = "route_waypoints"
    __table_args__ = (
        UniqueConstraint("route_id", "sequence", name="uq_route_waypoints_sequence"),
        CheckConstraint("sequence >= 1", name="ck_route_waypoints_sequence_positive"),
        CheckConstraint(
            "latitude_deg >= -90 AND latitude_deg <= 90",
            name="ck_route_waypoints_latitude_range",
        ),
        CheckConstraint(
            "longitude_deg >= -180 AND longitude_deg <= 180",
            name="ck_route_waypoints_longitude_range",
        ),
        CheckConstraint("altitude_m >= 0", name="ck_route_waypoints_altitude_nonnegative"),
        CheckConstraint("speed_mps > 0", name="ck_route_waypoints_speed_positive"),
        Index("ix_route_waypoints_route_id", "route_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    route_id: Mapped[int] = mapped_column(
        ForeignKey("routes.id", ondelete="CASCADE"), nullable=False
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    latitude_deg: Mapped[float] = mapped_column(Float, nullable=False)
    longitude_deg: Mapped[float] = mapped_column(Float, nullable=False)
    altitude_m: Mapped[float] = mapped_column(Float, nullable=False)
    speed_mps: Mapped[float] = mapped_column(Float, nullable=False)
    route: Mapped[Route] = relationship(back_populates="waypoints")
