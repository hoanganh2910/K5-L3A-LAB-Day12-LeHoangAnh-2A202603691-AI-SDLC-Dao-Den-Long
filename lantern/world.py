"""Standard maps for the three nights. Angles start at +X and run counter-clockwise."""

from __future__ import annotations

import math

from lantern import tuning as T


def duration_s(night: int) -> float:
    return {1: T.NIGHT1_DURATION_S, 2: T.NIGHT2_DURATION_S, 3: T.NIGHT3_DURATION_S}[night]


def shade_speed(night: int) -> float:
    return T.SHADE_SPEED_NIGHT3 if night == 3 else T.SHADE_SPEED


def shade_cap(night: int) -> int:
    return {1: 6, 2: 8, 3: 10}[night]


def ring(cx: float, cz: float, radius: float, count: int, start_deg: float, y: float = 0.0):
    step = 360.0 / count
    points = []
    for index in range(count):
        rad = math.radians(start_deg + index * step)
        points.append((cx + radius * math.cos(rad), y, cz + radius * math.sin(rad)))
    return points


def mote_points(night: int) -> list[tuple[float, float, float]]:
    if night == 1:
        return ring(0, 0, 12, 8, 0) + ring(0, 0, 33, 16, 0)
    if night == 2:
        points = []
        for cx, cz in ((0.0, 0.0), (70.0, 0.0)):
            points.extend(ring(cx, cz, 10, 4, 0))
            points.extend(ring(cx, cz, 22, 8, 0))
        return points
    points = ring(0, 0, 34, 18, 0, 0)
    points.extend((18 * math.cos(math.radians(deg)), 3.0, 18 * math.sin(math.radians(deg))) for deg in range(20, 161, 20))
    points.extend(ring(0, 0, 5, 4, 45, 6))
    return points


def shade_points(night: int) -> list[tuple[float, float, float]]:
    if night == 1:
        return ring(0, 0, 37, 12, 15)
    if night == 2:
        return ring(0, 0, 26, 8, 22.5) + ring(70, 0, 26, 8, 22.5)
    return ring(0, 0, 43, 16, 0)


def dew_points(night: int) -> list[tuple[float, float, float]]:
    if night == 2:
        return ring(0, 0, 16, 8, 0) + ring(70, 0, 16, 8, 0)
    if night == 3:
        return ring(0, 0, 28, 12, 0)
    return []


def lantern_specs(night: int) -> tuple[tuple[str, float, float, float], ...]:
    if night == 1:
        return (
            ("L1", 0.0, 0.0, 25.0),
            ("L2", 23.8, 0.0, 7.7),
            ("L3", 14.7, 0.0, -20.2),
            ("L4", -14.7, 0.0, -20.2),
            ("L5", -23.8, 0.0, 7.7),
        )
    if night == 2:
        return (
            ("L1", 0.0, 0.0, 20.0),
            ("L2", 17.0, 0.0, -10.0),
            ("L3", -17.0, 0.0, -10.0),
            ("L4", 70.0, 0.0, 20.0),
            ("L5", 87.0, 0.0, -10.0),
            ("L6", 53.0, 0.0, -10.0),
        )
    return (
        ("L1", 0.0, 6.0, 6.0),
        ("L2", 18.0, 3.0, 10.0),
        ("L3", -18.0, 3.0, 10.0),
        ("L4", 35.0, 0.0, -10.0),
        ("L5", -35.0, 0.0, -10.0),
        ("L6", 20.0, 0.0, -35.0),
        ("L7", -20.0, 0.0, -35.0),
    )


def charm_specs(night: int) -> tuple[tuple[str, float, float, float], ...]:
    if night == 2:
        return (("C1", 35.0, 0.0, 0.0),)
    if night == 3:
        return (("C1", 30.0, 0.0, 25.0), ("C2", -30.0, 0.0, 25.0))
    return ()


def pads(night: int) -> list[dict]:
    if night == 2:
        return [
            _pad((20.0, 0.0, 18.0), (70.0, 0.0, 0.0), 14.0, 24.0),
            _pad((50.0, 0.0, -18.0), (0.0, 0.0, 0.0), 14.0, 24.0),
        ]
    if night == 3:
        return [_pad((0.0, 3.0, 13.0), (0.0, 3.0, 12.0), 12.0, 8.0)]
    return []


def _pad(origin: tuple[float, float, float], target: tuple[float, float, float], vy: float, horizontal: float) -> dict:
    dx = target[0] - origin[0]
    dz = target[2] - origin[2]
    length = math.hypot(dx, dz) or 1.0
    return {
        "x": origin[0],
        "y": origin[1],
        "z": origin[2],
        "vy": vy,
        "vx": dx / length * horizontal,
        "vz": dz / length * horizontal,
    }


def surfaces(night: int, x: float, z: float) -> list[float]:
    """Walkable floor heights at this column. Empty means open air."""
    if night == 1:
        return [0.0] if math.hypot(x, z) <= 40.0 else []
    if night == 2:
        on_a = math.hypot(x, z) <= 28.0
        on_b = math.hypot(x - 70.0, z) <= 28.0
        on_bridge = 26.0 <= x <= 44.0 and -2.0 <= z <= 2.0
        return [0.0] if on_a or on_b or on_bridge else []
    if math.hypot(x, z) > 45.0:
        return []
    floors = [0.0]
    radius = math.hypot(x, z)
    ramp = _ramp_height(x, z)
    if ramp is not None:
        floors.append(ramp)
    if 12.0 <= radius <= 24.0 and z > 0.0:
        floors.append(3.0)
    if 2.0 < radius <= 8.0:
        floors.append(6.0)
    return floors


def _ramp_height(x: float, z: float) -> float | None:
    for deg in (30.0, 150.0):
        rad = math.radians(deg)
        forward_x = math.cos(rad)
        forward_z = math.sin(rad)
        along = x * forward_x + z * forward_z
        lateral = abs(x * forward_z - z * forward_x)
        if 24.0 <= along <= 30.0 and lateral <= 1.5:
            return (30.0 - along) / 6.0 * 3.0
    return None


def support(night: int, x: float, z: float, feet_y: float, grounded: bool) -> float | None:
    floors = surfaces(night, x, z)
    if not floors:
        return None
    if grounded:
        reachable = [height for height in floors if height <= feet_y + 0.25]
        return max(reachable) if reachable else None
    below = [height for height in floors if height <= feet_y + 0.02]
    return max(below) if below else None


def inside_bell(night: int, x: float, z: float, feet_y: float) -> bool:
    return night == 3 and feet_y >= 5.5 and math.hypot(x, z) <= 2.0


def gust_phase(sim_tick: int) -> tuple[str, int]:
    """Return calm/warn/active and the gust index. First gust starts at tick 1800."""
    if sim_tick < 1680:
        return "calm", 0
    cycle = sim_tick // 1800
    into = sim_tick % 1800
    if cycle == 0:
        return "warn", 1
    if into < 300:
        return "active", cycle
    if into >= 1680:
        return "warn", cycle + 1
    return "calm", cycle
