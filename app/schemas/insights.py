"""Route metrics and AI route review contracts."""

from typing import Literal

from pydantic import BaseModel


class RouteInsightsResponse(BaseModel):
    route_id: int
    route_name: str
    aircraft_registration: str | None
    waypoint_count: int
    leg_count: int
    total_distance_km: float
    estimated_duration_min: float
    min_altitude_m: float
    max_altitude_m: float
    min_speed_mps: float
    max_speed_mps: float
    aircraft_ceiling_m: float | None
    ceiling_margin_m: float | None
    max_vertical_rate_mps: float
    warnings: list[str]


class RouteReviewResponse(BaseModel):
    """Review of a route plan. ``source`` tells whether AI wrote it."""

    source: Literal["ai", "rules"]
    model: str | None = None
    summary: str
    strengths: list[str]
    risks: list[str]
    suggestions: list[str]
    insights: RouteInsightsResponse
    disclaimer: str = (
        "Revisión académica de un plan simulado. No sustituye la planificación "
        "ni la aprobación de un vuelo real."
    )
