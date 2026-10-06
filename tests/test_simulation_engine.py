from math import nan

import pytest

from app.simulation.engine import Waypoint, bearing_deg, distance_m, sample_path, validate_path


def point(lat: float, lon: float, altitude: float = 1000, speed: float = 100) -> Waypoint:
    return Waypoint(lat, lon, altitude, speed)


def test_distance_and_cardinal_bearings() -> None:
    origin = point(0, 0)
    assert distance_m(origin, point(0, 1)) == pytest.approx(111195.08, abs=0.1)
    assert bearing_deg(origin, point(0, 1)) == pytest.approx(90)
    assert bearing_deg(origin, point(1, 0)) == pytest.approx(0)


def test_midpoint_and_completion_are_deterministic() -> None:
    points = [point(0, 0, 1000), point(0, 1, 2000)]
    duration = distance_m(*points) / 100
    state = sample_path(points, duration / 2)
    assert state == sample_path(points, duration / 2)
    assert state.longitude_deg == pytest.approx(0.5)
    assert state.latitude_deg == pytest.approx(0, abs=1e-10)
    assert state.altitude_m == pytest.approx(1500)
    assert state.progress == pytest.approx(0.5)
    assert state.next_waypoint == 2
    assert state.heading_deg == pytest.approx(90)
    assert not state.completed

    final = sample_path(points, duration + 10)
    assert final.completed
    assert final.speed_mps == 0
    assert final.progress == 1
    assert final.next_waypoint is None
    assert final.longitude_deg == 1


def test_multiple_legs_change_speed_at_the_boundary() -> None:
    points = [point(0, 0, speed=100), point(0, 1, speed=200), point(1, 1)]
    duration = distance_m(points[0], points[1]) / 100
    state = sample_path(points, duration + 10)
    assert state.speed_mps == 200
    assert state.longitude_deg == pytest.approx(1)
    assert state.latitude_deg > 0
    assert state.next_waypoint == 3


def test_dateline_crossing_uses_shortest_arc() -> None:
    points = [point(0, 179), point(0, -179)]
    duration = distance_m(*points) / 100
    state = sample_path(points, duration / 2)
    assert abs(state.longitude_deg) == pytest.approx(180)
    assert state.duration_s == pytest.approx(2223.9016, abs=0.01)


@pytest.mark.parametrize("elapsed", [-1, nan, float("inf")])
def test_invalid_elapsed_time_is_rejected(elapsed: float) -> None:
    with pytest.raises(ValueError):
        sample_path([point(0, 0), point(0, 1)], elapsed)


def test_degenerate_and_antipodal_legs_are_rejected() -> None:
    with pytest.raises(ValueError, match="different horizontal"):
        validate_path([point(0, 0), point(0, 0, 2000)])
    with pytest.raises(ValueError, match="Antipodal"):
        validate_path([point(0, 0), point(0, 180)])
    with pytest.raises(ValueError, match="range"):
        point(91, 0)
