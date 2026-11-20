"""Night 1 rules, checked against Test Contract v1.0."""

import math

import pytest

from lantern.sim import FormatError, parse_inputs, run_simulation
from lantern.tuning import contract_dict

DT = 1.0 / 60.0


def quiet(**overrides):
    scenario = {
        "random_motes": False,
        "random_shades": False,
        "motes": [],
        "shades": [],
    }
    scenario.update(overrides)
    return scenario


def simulate(scenario=None, frames=None, ticks=60, seed=1, every=10):
    return run_simulation(seed, scenario, frames or [], ticks, every)


def events(lines, name=None):
    found = [line for line in lines if line["type"] == "event"]
    if name is None:
        return found
    return [line for line in found if line["name"] == name]


def snap(lines, tick):
    return next(line for line in lines if line["type"] == "snapshot" and line["tick"] == tick)


def test_contract_file_matches_tuning():
    import json
    from pathlib import Path

    on_disk = json.loads(Path("game.contract.json").read_text(encoding="utf-8"))
    assert on_disk == contract_dict()


def test_tick_zero_is_before_input_and_move_is_exact():
    lines = simulate(
        quiet(),
        frames=[{"tick": 0, "move": [0, 1]}],
        ticks=60,
        every=60,
    )
    assert lines[0]["tick"] == 0
    assert lines[0]["sim_tick"] == 0
    assert lines[0]["player"]["pos"] == [0.0, 0.0, 0.0]
    assert lines[0]["state"] == "playing"
    assert lines[0]["score"] == 0
    assert snap(lines, 60)["player"]["pos"][2] == 6.0
    assert lines[-1] == {"type": "end", "ticks": 60, "state": "playing", "score": 0}


def test_yaw_and_normalization():
    yaw = simulate(
        quiet(),
        frames=[{"tick": 0, "move": [0, 1], "cam_yaw_deg": 90}],
        ticks=60,
        every=60,
    )
    assert snap(yaw, 60)["player"]["pos"][0] == 6.0
    assert snap(yaw, 60)["player"]["pos"][2] == 0.0

    diagonal = simulate(
        quiet(),
        frames=[{"tick": 0, "move": [1, 1]}],
        ticks=60,
        every=60,
    )
    pos = snap(diagonal, 60)["player"]["pos"]
    assert pos[0] == 4.243
    assert pos[2] == 4.243


def test_stand_still_without_inputs():
    lines = simulate(quiet(), ticks=30, every=10)
    assert snap(lines, 30)["player"]["pos"] == [0.0, 0.0, 0.0]
    assert [line["tick"] for line in lines if line["type"] == "snapshot"] == [0, 10, 20, 30]


def test_pickup_radius_is_inclusive_and_capacity_blocks():
    picked = simulate(
        quiet(motes=[[0, 0, 1.5]]),
        ticks=1,
        every=10,
    )
    assert events(picked, "mote_picked") == [
        {"type": "event", "tick": 1, "name": "mote_picked", "data": {"carried": 1}}
    ]
    assert snap(picked, 0)["motes_active"] == 1
    assert picked[-1]["score"] == 10

    missed = simulate(quiet(motes=[[0, 0, 1.501]]), ticks=1)
    assert events(missed, "mote_picked") == []

    full = simulate(
        quiet(player={"pos": [0, 0, 0], "carried": 8, "flames": 3}, motes=[[0, 0, 0]]),
        ticks=1,
    )
    assert events(full, "mote_picked") == []
    assert full[-1]["score"] == 0


def test_interact_is_edge_triggered_and_lights_nearest_lantern():
    held = simulate(
        quiet(
            player={"pos": [0, 0, 0], "carried": 2, "flames": 3},
            lanterns=[{"id": "L1", "pos": [0, 0, 0], "deposited": 0, "lit": False}],
        ),
        frames=[{"tick": 0, "interact": True}],
        ticks=3,
        every=10,
    )
    deposits = events(held, "deposit")
    assert len(deposits) == 1
    assert deposits[0]["data"] == {"lantern_id": "L1", "amount": 2, "deposited": 2}
    assert events(held, "lantern_lit") == []

    pressed_twice = simulate(
        quiet(
            player={"pos": [0, 0, 0], "carried": 4, "flames": 3},
            lanterns=[
                {"id": "L1", "pos": [0, 0, 0]},
                {"id": "L2", "pos": [0, 0, 1]},
            ],
        ),
        frames=[
            {"tick": 0, "interact": True},
            {"tick": 1, "interact": False},
            {"tick": 2, "interact": True},
        ],
        ticks=3,
    )
    deposits = events(pressed_twice, "deposit")
    assert [line["data"]["lantern_id"] for line in deposits] == ["L1", "L2"]
    assert deposits[0]["data"]["amount"] == 3
    assert deposits[1]["data"]["amount"] == 1


def test_win_scores_lantern_time_and_flames_once():
    lines = simulate(
        quiet(
            player={"pos": [0, 0, 0], "carried": 3, "flames": 3},
            time_left_s=180,
            lanterns=[
                {"id": "L1", "pos": [0, 0, 0], "deposited": 0, "lit": False},
                {"id": "L2", "lit": True},
                {"id": "L3", "lit": True},
                {"id": "L4", "lit": True},
                {"id": "L5", "lit": True},
            ],
        ),
        frames=[{"tick": 0, "interact": True}],
        ticks=50,
        every=10,
    )
    assert events(lines, "lantern_lit")[0]["data"] == {"lantern_id": "L1"}
    assert events(lines, "game_over") == [
        {
            "type": "event",
            "tick": 1,
            "name": "game_over",
            "data": {"result": "won", "reason": "all_lit"},
        }
    ]
    assert lines[-1] == {"type": "end", "ticks": 1, "state": "won", "score": 339}


def test_prelit_lanterns_do_not_score_or_emit_events():
    lines = simulate(
        quiet(
            lanterns=[
                {"id": "L1", "lit": True},
                {"id": "L2", "lit": True},
                {"id": "L3", "lit": True},
                {"id": "L4", "lit": True},
                {"id": "L5", "lit": True},
            ]
        ),
        ticks=10,
    )
    assert lines[0]["state"] == "won"
    assert lines[0]["score"] == 0
    assert events(lines) == []
    assert lines[-1]["ticks"] == 0


def test_pulse_cost_radius_push_and_cooldown():
    stunned = simulate(
        quiet(
            player={"carried": 2, "flames": 3, "pos": [0, 0, 0]},
            shades=[{"id": "S1", "pos": [5, 0, 0]}, {"id": "S9", "pos": [8.1, 0, 0]}],
        ),
        frames=[{"tick": 0, "pulse": True}, {"tick": 1, "pulse": False}],
        ticks=1,
        every=1,
    )
    pulse = events(stunned, "pulse")
    assert pulse == [
        {"type": "event", "tick": 1, "name": "pulse", "data": {"stunned_ids": ["S1"]}}
    ]
    shade = snap(stunned, 0)  # tick 0 is before the pulse
    assert shade["shades"][0]["pos"][0] == 5.0
    after = [line for line in stunned if line["type"] == "snapshot"][-1]
    by_id = {item["id"]: item for item in after["shades"]}
    assert by_id["S1"]["state"] == "stunned"
    assert by_id["S1"]["pos"][0] == 9.0
    assert by_id["S1"]["pos"][1] == 1.0
    assert by_id["S9"]["state"] == "chase"
    assert after["player"]["carried"] == 1
    assert after["score"] == 15

    early = simulate(
        quiet(player={"carried": 2, "flames": 3, "pos": [0, 0, 0]}, shades=[{"pos": [5, 0, 0]}]),
        frames=[
            {"tick": 0, "pulse": True},
            {"tick": 1, "pulse": False},
            {"tick": 47, "pulse": True},
        ],
        ticks=48,
        every=100,
    )
    assert len(events(early, "pulse")) == 1

    ready = simulate(
        quiet(player={"carried": 2, "flames": 3, "pos": [0, 0, 0]}, shades=[{"pos": [3, 0, 0]}]),
        frames=[
            {"tick": 0, "pulse": True},
            {"tick": 1, "pulse": False},
            {"tick": 48, "pulse": True},
            {"tick": 49, "pulse": False},
        ],
        ticks=49,
        every=100,
    )
    assert len(events(ready, "pulse")) == 2
    assert ready[-1]["score"] == 30


def test_shade_chase_speed_safe_radius_and_hit():
    chased = simulate(
        quiet(shades=[{"id": "S1", "pos": [10, 0, 0]}]),
        ticks=60,
        every=60,
    )
    assert snap(chased, 60)["shades"][0]["pos"][0] == 6.5
    assert snap(chased, 60)["shades"][0]["state"] == "chase"

    safe = simulate(
        quiet(
            shades=[{"id": "S1", "pos": [20, 0, 0]}],
            lanterns=[{"id": "L1", "pos": [0, 0, 0], "lit": True}],
        ),
        ticks=400,
        every=400,
    )
    assert snap(safe, 400)["shades"][0]["pos"][0] == 6.0
    assert events(safe, "player_hit") == []

    unlit = simulate(
        quiet(
            shades=[{"id": "S1", "pos": [10, 0, 0]}],
            lanterns=[{"id": "L1", "pos": [0, 0, 0], "lit": False}],
        ),
        ticks=60,
        every=60,
    )
    assert snap(unlit, 60)["shades"][0]["pos"][0] == 6.5

    hit = simulate(
        quiet(player={"flames": 3, "carried": 4, "pos": [0, 0, 0]}, shades=[{"pos": [0, 0, 0]}, {"pos": [0, 0, 0]}]),
        ticks=1,
    )
    assert events(hit, "player_hit") == [
        {
            "type": "event",
            "tick": 1,
            "name": "player_hit",
            "data": {"by": "shade", "flames": 2, "dropped": 0},
        }
    ]

    still_safe = simulate(
        quiet(player={"flames": 3, "pos": [0, 0, 0]}, shades=[{"pos": [0, 0, 0]}]),
        ticks=60,
        every=60,
    )
    assert snap(still_safe, 60)["player"]["flames"] == 2

    second = simulate(
        quiet(player={"flames": 3, "pos": [0, 0, 0]}, shades=[{"pos": [0, 0, 0]}]),
        ticks=61,
        every=61,
    )
    assert snap(second, 61)["player"]["flames"] == 1


def test_loss_by_no_flames_and_dawn():
    dead = simulate(
        quiet(player={"flames": 1, "pos": [0, 0, 0]}, shades=[{"pos": [0, 0, 0]}]),
        ticks=30,
    )
    assert events(dead, "game_over")[0]["data"] == {"result": "lost", "reason": "no_flames"}
    assert dead[-1] == {"type": "end", "ticks": 1, "state": "lost", "score": 0}

    dawn = simulate(quiet(time_left_s=1), ticks=120, every=60)
    assert events(dawn, "game_over")[0]["data"] == {"result": "lost", "reason": "dawn"}
    assert dawn[-1]["ticks"] == 60
    assert dawn[-1]["state"] == "lost"
    assert snap(dawn, 60)["time_left_s"] == 0.0


def test_same_seed_is_byte_identical_and_spawn_uses_seed():
    scenario = {"random_motes": False, "random_shades": True, "motes": [], "shades": []}
    first = simulate(scenario, ticks=1200, seed=4, every=1200)
    second = simulate(scenario, ticks=1200, seed=4, every=1200)
    other = simulate(scenario, ticks=1200, seed=5, every=1200)
    assert first == second
    spawned = events(first, "shade_spawned")
    assert len(spawned) == 1
    assert spawned[0]["tick"] == 1200
    assert snap(first, 1200)["shades"] != snap(other, 1200)["shades"]


def test_jump_leaves_the_ground():
    lines = simulate(quiet(), frames=[{"tick": 0, "jump": True}], ticks=1, every=1)
    assert snap(lines, 1)["player"]["pos"][1] == round((6.5 + (-20) * DT) * DT, 3)


def test_walking_off_the_visual_island_is_not_a_fall():
    lines = simulate(quiet(), frames=[{"tick": 0, "move": [0, 1]}], ticks=600, every=600)
    assert events(lines, "player_hit") == []
    assert snap(lines, 600)["player"]["pos"][2] == 60.0


def test_malformed_inputs_and_scenario():
    with pytest.raises(FormatError):
        parse_inputs({"frames": [{"tick": 2}, {"tick": 2}]})
    with pytest.raises(FormatError):
        parse_inputs({"frames": [{"tick": 0, "move": [0, 2]}]})
    with pytest.raises(FormatError):
        simulate({"lanterns": [{"id": "L9"}]}, ticks=1)
    with pytest.raises(FormatError):
        simulate({"time_left_s": -1}, ticks=1)


def test_snapshot_lists_motes_and_five_lanterns():
    lines = simulate(quiet(motes=[[0, 0, 5]]), ticks=0, every=10)
    assert lines[0]["motes"] == [{"id": "M1", "pos": [0.0, 0.0, 5.0]}]
    assert [lantern["id"] for lantern in lines[0]["lanterns"]] == ["L1", "L2", "L3", "L4", "L5"]
    assert lines[-1]["ticks"] == 0


def test_default_night_is_winnable_on_paper():
    from lantern.sim import Sim
    from lantern.tuning import LANTERN_COST, PLAY_SEED

    sim = Sim.create(PLAY_SEED, None)
    assert len(sim.lanterns) == 5
    assert len(sim.motes) == 5 * LANTERN_COST
    assert len(sim.shades) == 2
    assert sim.state == "playing"
    assert all(math.hypot(mote.x, mote.z) > 1.5 for mote in sim.motes)


def test_floor_of_remaining_time_matches_formula():
    remaining = 180 - DT
    assert math.floor(remaining + 1e-9) == 179
