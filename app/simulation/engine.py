"""Academic spherical-Earth route interpolation using SI units.

This is a geometric simulator, not an operational flight-dynamics/ATC model.
Ground speed is constant per leg; altitude is interpolated linearly.
"""

from dataclasses import dataclass
from math import asin, atan2, cos, degrees, isfinite, pi, radians, sin, sqrt
from collections.abc import Sequence

EARTH_RADIUS_M = 6_371_008.8


@dataclass(frozen=True)
class Waypoint:
    latitude_deg: float
    longitude_deg: float
    altitude_m: float
    speed_mps: float

    def __post_init__(self) -> None:
        values = (self.latitude_deg, self.longitude_deg, self.altitude_m, self.speed_mps)
        if not all(isfinite(value) for value in values):
            raise ValueError("Waypoint values must be finite")
        if not -90 <= self.latitude_deg <= 90 or not -180 <= self.longitude_deg <= 180:
            raise ValueError("Waypoint coordinates are out of range")
        if self.altitude_m < 0 or self.speed_mps <= 0:
            raise ValueError("Altitude must be nonnegative and speed must be positive")


@dataclass(frozen=True)
class RouteState:
    latitude_deg: float
    longitude_deg: float
    altitude_m: float
    speed_mps: float
    heading_deg: float
    next_waypoint: int | None
    progress: float
    duration_s: float
    completed: bool


def distance_m(a: Waypoint, b: Waypoint) -> float:
    """Great-circle surface distance, using a mean Earth radius."""
    lat1, lat2 = radians(a.latitude_deg), radians(b.latitude_deg)
    delta_lat = lat2 - lat1
    delta_lon = radians(b.longitude_deg - a.longitude_deg)
    value = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    return 2 * EARTH_RADIUS_M * asin(sqrt(min(1.0, max(0.0, value))))


def bearing_deg(a: Waypoint, b: Waypoint) -> float:
    """Initial true-north bearing, clockwise in [0, 360)."""
    lat1, lat2 = radians(a.latitude_deg), radians(b.latitude_deg)
    delta_lon = radians(b.longitude_deg - a.longitude_deg)
    return degrees(
        atan2(
            sin(delta_lon) * cos(lat2),
            cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(delta_lon),
        )
    ) % 360


def validate_path(points: Sequence[Waypoint]) -> tuple[float, ...]:
    if len(points) < 2:
        raise ValueError("A route must have at least two waypoints")
    distances = tuple(distance_m(a, b) for a, b in zip(points, points[1:]))
    if any(distance < 0.001 for distance in distances):
        raise ValueError("Consecutive waypoints must have different horizontal positions")
    if any(distance > pi * EARTH_RADIUS_M - 1 for distance in distances):
        raise ValueError("Antipodal route legs are ambiguous and are not supported")
    return distances


def _destination(start: Waypoint, heading: float, distance: float) -> tuple[float, float]:
    lat, lon, angle = radians(start.latitude_deg), radians(start.longitude_deg), radians(heading)
    arc = distance / EARTH_RADIUS_M
    sin_lat = sin(lat) * cos(arc) + cos(lat) * sin(arc) * cos(angle)
    target_lat = asin(min(1.0, max(-1.0, sin_lat)))
    target_lon = lon + atan2(
        sin(angle) * sin(arc) * cos(lat),
        cos(arc) - sin(lat) * sin(target_lat),
    )
    return degrees(target_lat), (degrees(target_lon) + 180) % 360 - 180


def sample_path(points: Sequence[Waypoint], elapsed_s: float) -> RouteState:
    """Evaluate a route at a time without mutable state or wall-clock input."""
    if not isfinite(elapsed_s) or elapsed_s < 0:
        raise ValueError("Elapsed time must be finite and nonnegative")
    distances = validate_path(points)
    durations = tuple(
        distance / points[index].speed_mps for index, distance in enumerate(distances)
    )
    total_duration = sum(durations)
    total_distance = sum(distances)
    remaining = elapsed_s
    travelled = 0.0
    for index, (distance, duration) in enumerate(zip(distances, durations)):
        start, end = points[index], points[index + 1]
        if remaining < duration:
            fraction = remaining / duration
            lat, lon = _destination(start, bearing_deg(start, end), distance * fraction)
            altitude = start.altitude_m + (end.altitude_m - start.altitude_m) * fraction
            position = Waypoint(lat, lon, altitude, start.speed_mps)
            return RouteState(
                latitude_deg=lat,
                longitude_deg=lon,
                altitude_m=altitude,
                speed_mps=start.speed_mps,
                heading_deg=bearing_deg(position, end),
                next_waypoint=index + 2,
                progress=(travelled + distance * fraction) / total_distance,
                duration_s=total_duration,
                completed=False,
            )
        remaining -= duration
        travelled += distance
    end = points[-1]
    return RouteState(
        latitude_deg=end.latitude_deg,
        longitude_deg=end.longitude_deg,
        altitude_m=end.altitude_m,
        speed_mps=0.0,
        heading_deg=0.0,
        next_waypoint=None,
        progress=1.0,
        duration_s=total_duration,
        completed=True,
    )
