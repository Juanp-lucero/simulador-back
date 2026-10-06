"""Aircraft and route API schemas. Positions use WGS84 degrees and SI units."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.simulation.engine import Waypoint, validate_path


class AircraftWrite(BaseModel):
    registration: str = Field(min_length=3, max_length=15, pattern=r"^[A-Z0-9][A-Z0-9-]+$")
    model_name: str = Field(min_length=2, max_length=100)
    cruise_speed_mps: float = Field(gt=0, le=400)
    max_altitude_m: float = Field(gt=0, le=20000)

    @field_validator("registration", mode="before")
    @classmethod
    def normalize_registration(cls, value: object) -> object:
        return value.strip().upper() if isinstance(value, str) else value

    @field_validator("model_name", mode="before")
    @classmethod
    def normalize_model_name(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class AircraftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    registration: str
    model_name: str
    cruise_speed_mps: float
    max_altitude_m: float
    created_at: datetime
    updated_at: datetime


class WaypointWrite(BaseModel):
    latitude_deg: float = Field(ge=-90, le=90)
    longitude_deg: float = Field(ge=-180, le=180)
    altitude_m: float = Field(ge=0, le=20000)
    speed_mps: float = Field(gt=0, le=400)


class WaypointResponse(WaypointWrite):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sequence: int


class RouteWrite(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    aircraft_id: int | None = Field(default=None, ge=1)
    waypoints: list[WaypointWrite] = Field(min_length=2, max_length=100)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("waypoints")
    @classmethod
    def validate_geometry(cls, value: list[WaypointWrite]) -> list[WaypointWrite]:
        validate_path([
            Waypoint(point.latitude_deg, point.longitude_deg, point.altitude_m, point.speed_mps)
            for point in value
        ])
        return value


class RouteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    aircraft_id: int | None
    created_at: datetime
    updated_at: datetime
    waypoints: list[WaypointResponse]
