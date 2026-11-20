"""Frame-time summaries for the benchmark. Times are milliseconds."""

from __future__ import annotations

import math


def summarize(frame_ms: list[float]) -> dict:
    count = len(frame_ms)
    if count == 0:
        raise ValueError("no frames")
    total = sum(frame_ms)
    average = 1000.0 * count / total
    keep = max(1, math.ceil(0.01 * count))
    slowest = sorted(frame_ms, reverse=True)[:keep]
    low = 1000.0 / (sum(slowest) / keep)
    ordered = sorted(frame_ms)
    index = min(count - 1, max(0, math.ceil(0.95 * count) - 1))
    return {
        "frames": count,
        "avg_fps": average,
        "p1_low_fps": low,
        "frame_ms_p95": ordered[index],
    }
