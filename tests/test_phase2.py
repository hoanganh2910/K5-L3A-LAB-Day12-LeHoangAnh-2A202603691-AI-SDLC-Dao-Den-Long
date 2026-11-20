"""One headless scenario for each Phase 2 feature."""

import math

from lantern.sim import run_simulation
from lantern import world


def quiet(night=1, **overrides):
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


def simulate(scenario=None, frames=None, ticks=60, seed=1, every=1, night=1):
    return run_simulation(seed, scenario if scenario is not None else quiet(night), frames or [], ticks, every, night)


def events(lines, name):
    return [line for line in lines if line["type"] == "event" and line["name"] == name]


def snap(lines, tick):
    return next(line for line in lines if line["type"] == "snapshot" and line["tick"] == tick)


def test_dash_distance_direction_and_cooldown():
    lines = simulate(
        quiet(),
        frames=[
            {"tick": 0, "dash": True},
            {"tick": 1, "dash": False},
            {"tick": 89, "dash": True},
            {"tick": 90, "dash": False},
            {"tick": 91, "dash": True},
        ],
        ticks=103,
    )
    assert [event["tick"] for event in events(lines, "dash")] == [1, 92]
    assert snap(lines, 12)["player"]["pos"][2] == round(14.0 * 12 / 60.0, 3)
    assert snap(lines, 12)["player"]["pos"][1] == 0.0


def test_charm_refreshes_speed_and_dash():
    lines = simulate(
        quiet(player={"dash_cd_ticks": 80}, charms=[{"id": "C1", "pos": [0, 0, 0.5]}]),
        frames=[{"tick": 1, "dash": True}],
        ticks=2,
    )
    assert events(lines, "charm_picked")[0]["data"] == {"charm_id": "C1", "charm_ticks": 600}
    assert events(lines, "dash")[0]["tick"] == 2
    assert snap(lines, 1)["player"]["charm_s"] == 10.0
    assert snap(lines, 1)["charms"][0]["available"] is False


def test_drifter_steals_once_then_flees():
    lines = simulate(
        quiet(
            player={"carried": 5},
            drifters=[{"id": "D1", "pos": [0, 1, 1.0], "state": "chase"}],
        ),
        ticks=2,
    )
    steal = events(lines, "drifter_steal")[0]["data"]
    assert steal == {"drifter_id": "D1", "amount": 3, "carried": 2}
    assert snap(lines, 1)["drifters"][0]["state"] == "flee"
    assert snap(lines, 1)["drifters"][0]["stolen"] == 3
    assert events(lines, "drifter_steal").__len__() == 1


def test_pulse_makes_a_loaded_drifter_drop_motes():
    lines = simulate(
        quiet(
            player={"carried": 3},
            drifters=[{"id": "D1", "pos": [0, 1, 0.2], "state": "flee", "stolen": 3}],
        ),
        frames=[{"tick": 0, "pulse": True}],
        ticks=2,
    )
    dropped = events(lines, "drifter_drop")[0]["data"]
    assert dropped == {"drifter_id": "D1", "amount": 3}
    motes = [mote for mote in snap(lines, 1)["motes"] if mote["kind"] == "dropped"]
    assert len(motes) == 3
    assert motes[0]["pos"][0] == 0.0
    assert motes[0]["ttl_s"] == 8.0


def test_pause_freezes_sim_tick_then_resume_moves():
    lines = simulate(
        quiet(),
        frames=[
            {"tick": 0, "move": [0, 1], "pause": True},
            {"tick": 1, "pause": False},
            {"tick": 5, "pause": True},
        ],
        ticks=7,
    )
    assert events(lines, "paused")[0]["tick"] == 1
    assert snap(lines, 4)["state"] == "paused"
    assert snap(lines, 4)["sim_tick"] == 0
    assert snap(lines, 4)["player"]["pos"] == [0.0, 0.0, 0.0]
    assert events(lines, "resumed")[0]["tick"] == 6
    assert snap(lines, 7)["sim_tick"] == 2
    assert snap(lines, 7)["player"]["pos"][2] == round(6.0 * 2 / 60.0, 3)


def test_night2_pad_launches_toward_the_other_island():
    pad = world.pads(2)[0]
    lines = simulate(
        quiet(player={"pos": [pad["x"], pad["y"], pad["z"]]}),
        frames=[{"tick": 0, "move": [1, 0]}],
        ticks=2,
        night=2,
    )
    player = snap(lines, 1)["player"]
    assert player["pos"][1] > 0
    assert player["vel"][0] == round(pad["vx"], 3)
    assert player["vel"][2] == round(pad["vz"], 3)
    assert snap(lines, 1)["night"] == 2


def test_night3_wind_pushes_a_still_player():
    lines = simulate(quiet(wind_enabled=True), ticks=1800, every=60, night=3)
    before = snap(lines, 1680)["wind"]
    after = snap(lines, 1800)["wind"]
    assert before["active"] is False
    assert after["active"] is True
    assert after["dir_deg"] == before["dir_deg"]
    assert snap(lines, 1800)["player"]["pos"] != [0.0, 0.0, 0.0]


def test_safe_eject_takes_thirty_ticks_and_does_not_hit():
    lines = simulate(
        quiet(
            player={"pos": [0, 0, 0], "carried": 1},
            shades=[{"id": "S1", "pos": [0, 0, 0]}],
            lanterns=[{"id": "L1", "pos": [0, 0, 0], "deposited": 9}],
        ),
        frames=[{"tick": 0, "interact": True}],
        ticks=30,
    )
    assert events(lines, "player_hit") == []
    shade = snap(lines, 30)["shades"][0]
    assert shade["pos"][0] == 6.0
    assert lines[-1]["state"] == "playing"


def test_mote_respawn_tick_and_cap_skip(tmp_path=None):
    lines = simulate(
        {"random_motes": True, "random_shades": False, "random_drifters": False, "wind_enabled": False, "motes": [], "charms": []},
        ticks=240,
        every=240,
    )
    assert len(snap(lines, 0)["motes"]) == 0
    assert len(snap(lines, 240)["motes"]) == 1


def test_hit_drop_lands_on_the_ring_and_survives_into_the_next_tick():
    lines = simulate(
        quiet(player={"carried": 4}, shades=[{"id": "S1", "pos": [0.2, 0, 0]}]),
        ticks=2,
    )
    assert snap(lines, 1)["player"]["carried"] == 2
    dropped = snap(lines, 1)["motes"]
    assert len(dropped) == 2
    assert {mote["kind"] for mote in dropped} == {"dropped"}
    for mote in dropped:
        distance = math.hypot(mote["pos"][0], mote["pos"][2])
        assert 1.5 <= distance <= 2.5
    assert snap(lines, 2)["motes"][0]["ttl_s"] < 8.0


def test_full_night_headless_finishes_quickly():
    import time

    started = time.perf_counter()
    lines = run_simulation(1, {"random_drifters": False}, [], 21600, 600, 1)
    elapsed = time.perf_counter() - started
    assert elapsed < 30
    assert lines[-1]["type"] == "end"
    assert lines[-1]["state"] == "lost"


def test_two_nights_are_byte_stable():
    first = simulate(quiet(wind_enabled=True), ticks=30, night=3, seed=4)
    second = simulate(quiet(wind_enabled=True), ticks=30, night=3, seed=4)
    assert first == second
