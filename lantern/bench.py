"""On-screen Night 1 benchmark. Ursina is imported only when the command runs."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import sys
import time
from pathlib import Path

from lantern.memory import rss_mb
from lantern.metrics import summarize
from lantern.tuning import CONTRACT_VERSION


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m lantern bench")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument("--out", type=str, required=True)
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return int(code) if isinstance(code, int) else 1
    if args.duration <= 0:
        print("duration must be > 0", file=sys.stderr)
        return 2
    out_path = str(Path(args.out).resolve())
    started = time.perf_counter()
    from panda3d.core import ConfigVariableBool, loadPrcFileData

    loadPrcFileData("", "sync-video false")
    loadPrcFileData("", "fullscreen false")
    loadPrcFileData("", "win-size 1280 720")
    try:
        from ursina import AmbientLight, DirectionalLight, Text, Ursina, camera, color, scene, window
    except ImportError:
        print("Ursina is required to bench. Run: python3 -m pip install -r requirements.txt", file=sys.stderr)
        return 1
    app = Ursina(
        title="Dao Den Long bench - dang do, dung tat cua so",
        borderless=False,
        fullscreen=False,
        size=(1280, 720),
        development_mode=False,
        show_ursina_splash=False,
    )
    window.color = color.rgb32(14, 20, 48)
    window.fps_counter.enabled = False
    window.exit_button.enabled = False
    try:
        window.vsync = False
    except Exception:
        pass
    camera.fov = 68
    scene.fog_color = color.rgb32(27, 35, 80)
    scene.fog_density = (40, 130)
    sun = DirectionalLight(shadows=False, rotation=(50, -35, 0))
    sun.color = color.rgb32(255, 233, 176)
    ambient = AmbientLight()
    ambient.color = color.rgb32(14, 20, 48)
    from lantern.play import Game

    Game(
        color,
        Text,
        camera,
        scene,
        ambient,
        False,
        contract={
            "seed": args.seed,
            "duration": args.duration,
            "out": out_path,
            "started_at": started,
            "vsync_off": not bool(ConfigVariableBool("sync-video").getValue()),
            "renderer": _renderer(),
            "os": platform.platform(),
        },
    )
    print("bench window open, do not close it", flush=True)
    app.run()
    print("bench window closed", flush=True)
    return 0


def write_report(path: str, samples: list[float], load_ms: float, peak_mb: float | None, meta: dict) -> None:
    stats = summarize(samples)
    payload = {
        "contract_version": CONTRACT_VERSION,
        "avg_fps": round(stats["avg_fps"], 1),
        "p1_low_fps": round(stats["p1_low_fps"], 1),
        "frame_ms_p95": round(stats["frame_ms_p95"], 1),
        "frames": stats["frames"],
        "load_ms": int(round(load_ms)),
        "peak_mem_mb": None if peak_mb is None else round(peak_mb, 1),
        "vsync_off": bool(meta["vsync_off"]),
        "renderer": meta["renderer"],
        "os": meta["os"],
    }
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _renderer() -> str:
    try:
        ursina_version = importlib.metadata.version("ursina")
    except importlib.metadata.PackageNotFoundError:
        ursina_version = "unknown"
    try:
        panda_version = importlib.metadata.version("panda3d")
    except importlib.metadata.PackageNotFoundError:
        panda_version = "unknown"
    return f"Ursina {ursina_version} / Panda3D {panda_version}"


def sample_memory(current: float | None) -> float | None:
    reading = rss_mb()
    if reading is None:
        return current
    if current is None:
        return reading
    return max(current, reading)


if __name__ == "__main__":
    sys.exit(main())
