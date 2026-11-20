"""The standard benchmark scene. No Ursina import."""

from __future__ import annotations

import math
import random


def even_points(count: int, seed: int, radius: float) -> list[tuple[float, float, float]]:
    """Spread points across a disc. The seed only rotates the pattern."""
    rng = random.Random(seed)
    spin = rng.random() * math.tau
    golden = math.pi * (3 - math.sqrt(5))
    points = []
    for index in range(count):
        distance = radius * math.sqrt((index + 0.5) / count)
        theta = spin + index * golden
        points.append((distance * math.cos(theta), 0.0, distance * math.sin(theta)))
    return points


def bench_scenario(seed: int) -> dict:
    shades = even_points(200, seed, 36.0)
    motes = even_points(100, seed + 1, 18.0)
    return {
        "random_motes": False,
        "random_shades": False,
        "random_drifters": False,
        "wind_enabled": False,
        "player": {"pos": [0, 0, 0], "carried": 0, "flames": 3},
        "motes": motes,
        "shades": [
            {"id": f"S{index}", "pos": list(pos), "state": "wander"}
            for index, pos in enumerate(shades, start=1)
        ],
        "drifters": [],
        "charms": [],
        "lanterns": [
            {"id": "L1", "lit": True, "fuel": 100},
            {"id": "L2", "lit": True, "fuel": 100},
            {"id": "L3", "lit": True, "fuel": 100},
        ],
    }
