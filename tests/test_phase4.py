"""Phase 4 release checks that do not open a window."""

import json
import random

from lantern.benchscene import bench_scenario, even_points
from lantern.keys import DEFAULT_KEYS, assign_key, clean_keys
from lantern.leaderboard import add_entry, export_payload, rank, valid_name
from lantern.metrics import summarize
from lantern.sim import Sim
from lantern.soak import night_input


def test_benchmark_math():
    stats = summarize([10, 10, 10, 10, 50])
    assert stats["frames"] == 5
    assert stats["avg_fps"] == 1000 * 5 / 90
    assert stats["p1_low_fps"] == 1000 / 50
    assert stats["frame_ms_p95"] == 50


def test_bench_scene_is_fixed_and_does_not_play_the_night_rules():
    scene = bench_scenario(42)
    assert len(scene["shades"]) == 200
    assert len(scene["motes"]) == 100
    assert all(shade["state"] == "wander" for shade in scene["shades"])
    assert even_points(200, 42, 36) == even_points(200, 42, 36)
    assert max(point[0] ** 2 + point[2] ** 2 for point in even_points(200, 42, 36)) < 40 ** 2
    sim = Sim.create(42, scene, 1)
    sim.bench = True
    fuel = sim.lanterns[0].fuel_units
    carried = sim.carried
    origin = (sim.shades[-1].x, sim.shades[-1].z)
    for _ in range(30):
        sim.step()
    assert sim.state == "playing"
    assert sim.lanterns[0].fuel_units == fuel
    assert sim.carried == carried
    assert (sim.shades[-1].x, sim.shades[-1].z) != origin
    assert [lantern.id for lantern in sim.lanterns if lantern.lit] == ["L1", "L2", "L3"]


def test_key_bindings_reject_duplicates_and_restore():
    keys = dict(DEFAULT_KEYS)
    updated, error = assign_key(keys, "jump", "e")
    assert updated is None
    assert error
    updated, error = assign_key(keys, "jump", "j")
    assert error is None
    assert updated["jump"] == "j"
    restored = clean_keys({})
    assert restored == DEFAULT_KEYS


def test_leaderboard_keeps_ten_and_breaks_ties_by_time(tmp_path):
    path = tmp_path / "board.json"
    assert valid_name("May_01")
    assert valid_name("Mây")
    assert not valid_name("no")
    assert not valid_name("has space")
    for index in range(12):
        add_entry(
            {
                "name": f"P{index:02d}",
                "score": 100 if index < 2 else index,
                "nights_won": 1,
                "achieved_at": f"2026-11-20T16:{index:02d}:00+07:00",
                "seed": 1,
            },
            path,
        )
    entries = export_payload(path)["entries"]
    assert len(entries) == 10
    assert entries[0]["name"] == "P00"
    assert entries[1]["name"] == "P01"
    assert [item["score"] for item in entries] == sorted((item["score"] for item in entries), reverse=True)
    tied = rank(
        [
            {"name": "late", "score": 5, "achieved_at": "2026-11-20T18:00:00+07:00"},
            {"name": "early", "score": 5, "achieved_at": "2026-11-20T17:00:00+07:00"},
        ]
    )
    assert [item["name"] for item in tied] == ["early", "late"]


def test_soak_inputs_follow_the_seed_and_one_night_finishes(tmp_path):
    first = random.Random(8)
    second = random.Random(8)
    move_a, buttons_a = night_input(first, 0, [0.0, 0.0])
    move_b, buttons_b = night_input(second, 0, [0.0, 0.0])
    assert move_a == move_b
    assert buttons_a == buttons_b
    from lantern.soak import run_soak

    report = run_soak(7, 1)
    assert report["nights"] == 1
    assert report["crashes"] == 0
    assert report["results"][0] in ("won", "lost")
    assert report["mem_start_mb"] is not None
    assert report["mem_end_mb"] <= report["mem_start_mb"] * 1.2
