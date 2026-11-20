"""Night rules against Test Contract v1.2, including the Phase 1 behaviors with standard numbers."""

import json
from pathlib import Path

from lantern.sim import FormatError, parse_inputs, parse_scenario, run_simulation
from lantern.tuning import contract_dict

DT = 1.0 / 60.0


def quiet(**overrides):
    scenario = {
        "random_motes": False,
        "random_shades": False,
        "random_drifters": False,
        "wind_enabled": False,
        "motes": [],
        "shades": [],
        "drifters": [],
        "charms": [],
    }
    scenario.update(overrides)
    return scenario


def simulate(scenario=None, frames=None, ticks=60, seed=1, every=10, night=1):
    return run_simulation(seed, scenario, frames or [], ticks, every, night)


def events(lines, name=None):
    found = [line for line in lines if line["type"] == "event"]
    if name is None:
        return found
    return [line for line in found if line["name"] == name]


def snap(lines, tick):
    return next(line for line in lines if line["type"] == "snapshot" and line["tick"] == tick)


def test_contract_file_matches_tuning():
    on_disk = json.loads(Path("game.contract.json").read_text(encoding="utf-8"))
    assert on_disk == contract_dict()
    assert on_disk["contract_version"] == "1.2"
    tuning = on_disk["tuning"]
    assert tuning["player_speed"] == 6.0
    assert tuning["carry_capacity"] == 10
    assert tuning["lantern_cost"] == 10
    assert tuning["pickup_radius"] == 1.0
    assert tuning["pulse_cost"] == 3
    assert tuning["pulse_radius"] == 5.0
    assert tuning["night1_duration_s"] == 240
    assert tuning["dash_speed"] == 14.0
    assert tuning["night2_duration_s"] == 270
    assert tuning["night3_duration_s"] == 300
    assert tuning["fuel_max"] == 100
    assert tuning["fuel_decay_per_s"] == 1.0
    assert tuning["fuel_per_mote"] == 10
    assert tuning["relight_cost"] == 5
    assert tuning["win_ratio"] == 0.6
    assert tuning["drain_per_s"] == 5
    assert tuning["low_fuel_threshold"] == 30
    assert tuning["capacity_max"] == 20
    assert tuning["fall_enabled"] is True
    assert tuning["score"]["per_mote"] == 5
    assert tuning["score"]["per_stun"] == 5
    assert tuning["score"]["per_second_left"] == 0
    assert tuning["score"]["per_flame_left"] == 50


def test_tick_zero_is_before_input_and_move_is_exact():
    lines = simulate(quiet(), frames=[{"tick": 0, "move": [0, 1]}], ticks=60, every=60)
    assert lines[0]["tick"] == 0
    assert lines[0]["sim_tick"] == 0
    assert lines[0]["player"]["pos"] == [0.0, 0.0, 0.0]
    assert lines[0]["state"] == "playing"
    assert lines[0]["score"] == 0
    assert lines[0]["night"] == 1
    assert snap(lines, 60)["player"]["pos"][2] == 6.0
    assert lines[-1]["ticks"] == 60


def test_yaw_and_normalization():
    yaw = simulate(quiet(), frames=[{"tick": 0, "move": [0, 1], "cam_yaw_deg": 90}], ticks=60, every=60)
    assert snap(yaw, 60)["player"]["pos"][0] == 6.0
    assert snap(yaw, 60)["player"]["pos"][2] == 0.0
    diagonal = simulate(quiet(), frames=[{"tick": 0, "move": [1, 1]}], ticks=60, every=60)
    pos = snap(diagonal, 60)["player"]["pos"]
    assert pos[0] == 4.243
    assert pos[2] == 4.243


def test_stand_still_without_inputs():
    lines = simulate(quiet(), ticks=30, every=10)
    assert snap(lines, 30)["player"]["pos"] == [0.0, 0.0, 0.0]
    assert [line["tick"] for line in lines if line["type"] == "snapshot"] == [0, 10, 20, 30]


def test_pickup_radius_height_and_capacity():
    picked = simulate(quiet(motes=[[0, 0, 1.0]]), ticks=1, every=10)
    assert events(picked, "mote_picked")[0]["data"] == {"carried": 1}
    assert picked[-1]["score"] == 0
    missed = simulate(quiet(motes=[[0, 0, 1.001]]), ticks=1, every=10)
    assert events(missed, "mote_picked") == []
    high = simulate(
        quiet(player={"pos": [0, 3, 18]}, motes=[[0, 0, 18]]),
        ticks=1,
        every=10,
        night=3,
    )
    assert events(high, "mote_picked") == []
    full = simulate(
        quiet(player={"carried": 10}, motes=[[0, 0, 0.5]]),
        ticks=1,
        every=10,
    )
    assert events(full, "mote_picked") == []


def test_deposit_scores_and_lights_the_nearest_lantern():
    scenario = quiet(
        player={"pos": [0, 0, 0], "carried": 10},
        lanterns=[
            {"id": "L1", "pos": [0, 0, 0], "deposited": 0},
            {"id": "L2", "pos": [0, 0, 1], "deposited": 0},
        ],
    )
    lines = simulate(
        scenario,
        frames=[{"tick": 0, "interact": True}, {"tick": 1, "interact": False}, {"tick": 2, "interact": True}],
        ticks=3,
        every=1,
    )
    deposits = events(lines, "deposit")
    assert deposits[0]["data"] == {"lantern_id": "L1", "amount": 10, "deposited": 10}
    assert events(lines, "lantern_lit")[0]["data"] == {"lantern_id": "L1", "relight": False}
    assert snap(lines, 1)["score"] == 150
    assert lines[-1]["state"] == "playing"
    assert len(deposits) == 1


def test_prelit_lanterns_do_not_score_or_emit_events():
    # Phase 3 replaces the old "all lit at setup wins immediately" rule.
    lines = simulate(
        quiet(lanterns=[{"id": f"L{i}", "lit": True} for i in range(1, 6)]),
        ticks=0,
    )
    assert events(lines) == []
    assert lines[0]["state"] == "playing"
    assert lines[0]["score"] == 0
    assert all(lantern["fuel"] == 100.0 and lantern["ever_lit"] for lantern in lines[0]["lanterns"])


def test_dawn_survived_replaces_the_early_all_lit_win():
    # The old test won on tick 1 with a time bonus. A night now ends only at dawn or at 0 flames.
    lines = simulate(
        quiet(
            time_left_s=1,
            player={"flames": 3},
            lanterns=[{"id": f"L{i}", "lit": True} for i in range(1, 4)],
        ),
        ticks=60,
        every=60,
    )
    assert lines[-1]["state"] == "won"
    assert lines[-1]["ticks"] == 60
    assert lines[-1]["score"] == 3 * (50 + 99) + 3 * 50
    assert events(lines, "game_over")[0]["data"] == {"result": "won", "reason": "dawn_survived"}


def test_pulse_stuns_within_5m_and_cools_down_for_3s():
    lines = simulate(
        quiet(player={"carried": 6}, shades=[{"id": "S1", "pos": [0, 0, 3]}]),
        frames=[{"tick": 0, "pulse": True}, {"tick": 1, "pulse": False}, {"tick": 180, "pulse": True}],
        ticks=181,
        every=15,
    )
    pulses = events(lines, "pulse")
    assert pulses[0]["tick"] == 1
    assert pulses[0]["data"] == {"stunned_ids": ["S1"]}
    assert pulses[1]["tick"] == 181
    assert snap(lines, 15)["shades"][0]["pos"][2] == 7.0
    assert snap(lines, 15)["shades"][0]["state"] == "stunned"
    assert snap(lines, 15)["score"] == 5


def test_shade_chase_speed_safe_radius_and_one_hit():
    chase = simulate(
        quiet(shades=[{"id": "S1", "pos": [10, 0, 0]}]),
        ticks=60,
        every=60,
    )
    assert snap(chase, 60)["shades"][0]["pos"][0] == 6.0
    safe = simulate(
        quiet(
            shades=[{"id": "S1", "pos": [10, 0, 0]}],
            lanterns=[{"id": "L1", "pos": [0, 0, 0], "lit": True}],
        ),
        ticks=120,
        every=60,
    )
    assert snap(safe, 120)["shades"][0]["pos"][0] == 6.0
    hit = simulate(
        quiet(player={"carried": 5}, shades=[{"id": "S1", "pos": [0.5, 0, 0]}]),
        ticks=1,
        every=1,
    )
    blow = events(hit, "player_hit")[0]["data"]
    assert blow["by"] == "shade"
    assert blow["flames"] == 2
    assert blow["dropped"] == 2
    assert "lost" not in blow
    again = simulate(
        quiet(player={"carried": 4}, shades=[{"id": "S1", "pos": [0.4, 0, 0], "state": "chase"}]),
        ticks=90,
        every=90,
    )
    assert len(events(again, "player_hit")) == 1
    assert snap(again, 90)["player"]["flames"] == 2


def test_loss_by_no_flames_and_by_dawn():
    dead = simulate(quiet(player={"flames": 0}), ticks=5, every=5)
    assert dead[-1]["state"] == "lost"
    assert dead[-1]["ticks"] == 0
    dawn = simulate(quiet(time_left_s=1), ticks=120, every=60)
    over = events(dawn, "game_over")[0]
    assert over["tick"] == 60
    assert over["data"] == {"result": "lost", "reason": "dawn"}


def test_same_seed_spawns_the_same_shades():
    first = simulate({"random_motes": False, "random_drifters": False, "wind_enabled": False, "charms": []}, ticks=300, every=300)
    second = simulate({"random_motes": False, "random_drifters": False, "wind_enabled": False, "charms": []}, ticks=300, every=300)
    assert first == second
    spawned = events(first, "shade_spawned")
    assert [event["data"]["id"] for event in spawned] == ["S1", "S2"]
    assert snap(first, 300)["shades"][0]["state"] == "spawning"


def test_jump_only_from_the_ground():
    lines = simulate(quiet(), frames=[{"tick": 0, "jump": True}], ticks=1, every=1)
    expected = round((7.0 - 20.0 / 60.0) / 60.0, 3)
    assert snap(lines, 1)["player"]["pos"][1] == expected
    assert snap(lines, 1)["player"]["grounded"] is False


def test_snapshot_shape_and_five_lanterns():
    lines = simulate(ticks=0, every=10)
    shot = lines[0]
    assert shot["player"]["vel"] == [0.0, 0.0, 0.0]
    assert shot["wind"] == {"active": False, "dir_deg": 0.0}
    assert len(shot["lanterns"]) == 5
    assert len(shot["motes"]) == 20
    assert shot["motes"][0]["kind"] == "random"
    assert shot["motes"][0]["ttl_s"] is None
    assert "drifters" in shot and "charms" in shot


def test_malformed_inputs_and_scenario():
    import pytest

    with pytest.raises(FormatError):
        parse_inputs({"frames": [{"tick": 1}, {"tick": 1}]})
    with pytest.raises(FormatError):
        parse_scenario({"motes": "nope"}, 1)


def test_walking_off_the_island_falls():
    lines = simulate(
        quiet(player={"pos": [41, 0, 0], "carried": 4}),
        ticks=140,
        every=1,
    )
    fall = events(lines, "player_hit")[0]
    assert fall["data"]["by"] == "fall"
    assert fall["data"]["lost"] == 4
    assert fall["data"]["flames"] == 2
    home = next(line for line in lines if line["type"] == "snapshot" and line["player"]["pos"] == [0.0, 0.0, 0.0] and line["tick"] > 0)
    assert home["player"]["invuln"] > 0
    assert home["sim_tick"] - fall["tick"] == 60
