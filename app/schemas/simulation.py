"""Stateless simulation preview contracts."""

from typing import Annotated

from pydantic import BaseModel, Field, field_validator


class SimulationPreviewRequest(BaseModel):
    route_ids: list[Annotated[int, Field(ge=1)]] = Field(min_length=1, max_length=25)
    elapsed_s: float = Field(default=0, ge=0, le=86400)

    @field_validator("route_ids")
    @classmethod
    def unique_routes(cls, value: list[int]) -> list[int]:
        if len(set(value)) != len(value):
            raise ValueError("Route IDs must be unique")
        return value


class AircraftStateResponse(BaseModel):
    aircraft_id: int
    registration: str
    route_id: int
    route_name: str
    latitude_deg: float
    longitude_deg: float
    altitude_m: float
    speed_mps: float
    heading_deg: float
    next_waypoint: int | None
    progress: float
    duration_s: float
    completed: bool


class SimulationPreviewResponse(BaseModel):
    elapsed_s: float
    states: list[AircraftStateResponse]
