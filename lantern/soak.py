"""Ten nights in one process. This module does not import Ursina."""

from __future__ import annotations

import argparse
import gc
import json
import math
import random
import sys
import time

from lantern.memory import rss_mb
from lantern.sim import Sim


def night_input(rng: random.Random, tick: int, move: list[float]) -> tuple[list[float], dict]:
    if tick % 30 == 0:
        angle = rng.random() * math.tau
        move = [math.cos(angle), math.sin(angle)]
    buttons = {
        "jump": rng.random() < 0.05,
        "dash": rng.random() < 0.03,
        "pulse": rng.random() < 0.02,
        "interact": rng.random() < 0.10,
        "pause": False,
    }
    return move, buttons


def run_soak(seed: int, nights: int) -> dict:
    started = time.perf_counter()
    crashes = 0
    results: list[str] = []
    mem_start = None
    for index in range(1, nights + 1):
        night = ((index - 1) % 3) + 1
        sim = None
        try:
            sim = Sim.create(seed + index, None, night)
            if mem_start is None:
                mem_start = rss_mb()
            rng = random.Random(seed + index)
            move = [0.0, 0.0]
            limit = int(round(sim.duration_s * 60)) + 2
            while sim.state == "playing" and sim.tick < limit:
                move, buttons = night_input(rng, sim.tick, move)
                sim.set_input(move, 0.0, buttons)
                sim.step()
            results.append(sim.state if sim.state in ("won", "lost") else "lost")
        except Exception:
            crashes += 1
            results.append("lost")
        finally:
            sim = None
            gc.collect()
    mem_end = rss_mb()
    if mem_start is None:
        mem_start = mem_end
    return {
        "nights": nights,
        "crashes": crashes,
        "results": results,
        "mem_start_mb": None if mem_start is None else round(mem_start, 1),
        "mem_end_mb": None if mem_end is None else round(mem_end, 1),
        "duration_s": round(time.perf_counter() - started, 1),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m lantern soak")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--nights", type=int, required=True)
    parser.add_argument("--out", type=str, required=True)
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return int(code) if isinstance(code, int) else 1
    if args.nights < 1:
        print("nights must be >= 1", file=sys.stderr)
        return 2
    report = run_soak(args.seed, args.nights)
    try:
        with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    except OSError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(
        f"soak nights {report['nights']} crashes {report['crashes']} "
        f"mem {report['mem_start_mb']} -> {report['mem_end_mb']} in {report['duration_s']}s"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
