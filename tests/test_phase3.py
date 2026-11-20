"""Headless scenarios for the Phase 3 fuel, drain, and dawn rules."""

from lantern.sim import run_simulation


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


def simulate(scenario=None, frames=None, ticks=60, seed=1, every=60):
    return run_simulation(seed, scenario if scenario is not None else quiet(), frames or [], ticks, every)


def events(lines, name):
    return [line for line in lines if line["type"] == "event" and line["name"] == name]


def snap(lines, tick):
    return next(line for line in lines if line["type"] == "snapshot" and line["tick"] == tick)


def lantern(lines, tick, lantern_id):
    return next(item for item in snap(lines, tick)["lanterns"] if item["id"] == lantern_id)


def test_fuel_decays_one_per_second_and_then_goes_out():
    burning = simulate(quiet(lanterns=[{"id": "L1", "pos": [0, 0, 0], "lit": True}]), ticks=60)
    assert lantern(burning, 60, "L1")["fuel"] == 99.0
    assert lantern(burning, 60, "L1")["lit"] is True
    dying = simulate(quiet(lanterns=[{"id": "L1", "pos": [0, 0, 0], "lit": True, "fuel": 1}]), ticks=60, every=1)
    assert events(dying, "lantern_out")[0]["tick"] == 60
    assert events(dying, "lantern_out")[0]["data"] == {"lantern_id": "L1"}
    gone = lantern(dying, 60, "L1")
    assert gone["lit"] is False
    assert gone["fuel"] == 0.0
    assert gone["deposited"] == 0
    assert gone["ever_lit"] is True


def test_refuel_tops_up_and_a_full_lantern_is_skipped():
    lines = simulate(
        quiet(
            player={"pos": [0, 0, 0], "carried": 3},
            lanterns=[{"id": "L1", "pos": [0, 0, 0], "lit": True, "fuel": 90}],
        ),
        frames=[{"tick": 0, "interact": True}],
        ticks=1,
        every=1,
    )
    assert events(lines, "refuel")[0]["data"] == {"lantern_id": "L1", "amount": 2, "fuel": 100.0}
    assert snap(lines, 1)["score"] == 10
    full = simulate(
        quiet(
            player={"pos": [0, 0, 0], "carried": 10},
            lanterns=[
                {"id": "L1", "pos": [0, 0, 0], "lit": True, "fuel": 6001 / 60},
                {"id": "L2", "pos": [0, 0, 1], "deposited": 0},
            ],
        ),
        frames=[{"tick": 0, "interact": True}],
        ticks=1,
        every=1,
    )
    assert events(full, "refuel") == []
    assert events(full, "deposit")[0]["data"]["lantern_id"] == "L2"


def test_relight_costs_five_and_scores_less_than_the_first_light():
    lines = simulate(
        quiet(
            player={"pos": [0, 0, 0], "carried": 5},
            lanterns=[{"id": "L1", "pos": [0, 0, 0], "lit": False, "ever_lit": True}],
        ),
        frames=[{"tick": 0, "interact": True}],
        ticks=1,
        every=1,
    )
    assert events(lines, "deposit")[0]["data"] == {"lantern_id": "L1", "amount": 5, "deposited": 5}
    assert events(lines, "lantern_lit")[0]["data"] == {"lantern_id": "L1", "relight": True}
    lit = lantern(lines, 1, "L1")
    assert lit["fuel"] == 100.0
    assert lit["relit_count"] == 1
    assert snap(lines, 1)["score"] == 65
    short = simulate(
        quiet(
            player={"pos": [0, 0, 0], "carried": 5},
            lanterns=[{"id": "L1", "pos": [0, 0, 0], "ever_lit": False}],
        ),
        frames=[{"tick": 0, "interact": True}],
        ticks=1,
        every=1,
    )
    assert events(short, "lantern_lit") == []
    assert lantern(short, 1, "L1")["deposited"] == 5


def test_capacity_grows_with_successful_lights_and_caps_at_20():
    grown = simulate(quiet(player={"successful_lights": 1, "carried": 12}, motes=[[0, 0, 0.5]]), ticks=1, every=1)
    assert snap(grown, 0)["player"]["capacity"] == 12
    assert events(grown, "mote_picked") == []
    capped = simulate(quiet(player={"successful_lights": 8}), ticks=0)
    assert capped[0]["player"]["capacity"] == 20


def test_shade_drains_fuel_then_chases_inside_six_metres():
    lines = simulate(
        quiet(
            player={"pos": [0, 0, 30]},
            lanterns=[{"id": "L1", "pos": [0, 0, 0], "lit": True, "fuel": 29}],
            shades=[{"id": "S1", "pos": [0, 0, 0], "state": "drain", "target_lantern_id": "L1"}],
        ),
        ticks=60,
        every=60,
    )
    assert lantern(lines, 60, "L1")["fuel"] == 23.0
    assert events(lines, "fuel_drain")[0]["data"] == {"lantern_id": "L1", "shade_id": "S1", "fuel": 23.0}
    assert snap(lines, 60)["shades"][0]["state"] == "drain"
    chase = simulate(
        quiet(
            player={"pos": [0, 0, 5]},
            lanterns=[{"id": "L1", "pos": [0, 0, 0], "lit": True, "fuel": 20}],
            shades=[{"id": "S1", "pos": [0, 0, 0], "state": "drain", "target_lantern_id": "L1"}],
        ),
        ticks=1,
        every=1,
    )
    assert snap(chase, 1)["shades"][0]["state"] == "chase"


def test_low_fuel_loses_the_safe_zone_until_it_is_refilled():
    open_zone = simulate(
        quiet(
            player={"pos": [0, 0, 0]},
            lanterns=[{"id": "L1", "pos": [0, 0, 0], "lit": True, "fuel": 20}],
            shades=[{"id": "S1", "pos": [3, 0, 0], "state": "chase"}],
        ),
        ticks=0,
    )
    assert open_zone[0]["shades"][0]["pos"][0] == 3.0
    held = simulate(
        quiet(
            lanterns=[{"id": "L1", "pos": [0, 0, 0], "lit": True, "fuel": 30}],
            shades=[{"id": "S1", "pos": [3, 0, 0], "state": "chase"}],
        ),
        ticks=0,
    )
    assert held[0]["shades"][0]["pos"][0] == 6.0
    refilled = simulate(
        quiet(
            player={"pos": [0, 0, 0], "carried": 2},
            lanterns=[{"id": "L1", "pos": [0, 0, 0], "lit": True, "fuel": 20}],
            shades=[{"id": "S1", "pos": [4, 0, 0], "state": "wander"}],
        ),
        frames=[{"tick": 0, "interact": True}],
        ticks=30,
        every=30,
    )
    assert snap(refilled, 30)["shades"][0]["pos"][0] == 6.0
    assert events(refilled, "player_hit") == []


def test_wander_picks_the_weak_lantern_and_pulse_pays_more_for_a_drain():
    lines = simulate(
        quiet(
            player={"pos": [0, 0, 40]},
            lanterns=[{"id": "L1", "pos": [0, 0, 0], "lit": True, "fuel": 20}],
            shades=[{"id": "S1", "pos": [10, 0, 0], "state": "wander"}],
        ),
        ticks=60,
        every=60,
    )
    assert snap(lines, 60)["shades"][0]["pos"][0] == 6.0
    assert snap(lines, 60)["shades"][0]["state"] == "wander"
    stunned = simulate(
        quiet(
            player={"pos": [0, 0, 0], "carried": 3},
            lanterns=[{"id": "L1", "pos": [0, 0, 1], "lit": True, "fuel": 20}],
            shades=[{"id": "S1", "pos": [0, 0, 1], "state": "drain", "target_lantern_id": "L1"}],
        ),
        frames=[{"tick": 0, "pulse": True}],
        ticks=1,
        every=1,
    )
    assert events(stunned, "pulse")[0]["data"] == {"stunned_ids": ["S1"]}
    assert snap(stunned, 1)["score"] == 15
    assert snap(stunned, 1)["shades"][0]["state"] == "stunned"


def test_too_few_lanterns_at_dawn_is_a_loss_and_all_lit_does_not_end_early():
    short = simulate(
        quiet(time_left_s=1, lanterns=[{"id": f"L{i}", "lit": True} for i in range(1, 3)]),
        ticks=60,
        every=60,
    )
    assert events(short, "game_over")[0]["data"] == {"result": "lost", "reason": "dawn"}
    early = simulate(
        quiet(lanterns=[{"id": f"L{i}", "lit": True} for i in range(1, 6)]),
        ticks=5,
        every=5,
    )
    assert early[-1]["state"] == "playing"
    assert events(early, "game_over") == []
    last = simulate(
        quiet(
            time_left_s=1 / 60,
            player={"flames": 1},
            lanterns=[{"id": f"L{i}", "lit": True} for i in range(1, 4)],
            shades=[{"id": "S1", "pos": [0.5, 0, 0], "state": "chase"}],
        ),
        ticks=1,
        every=1,
    )
    assert events(last, "game_over")[0]["data"] == {"result": "lost", "reason": "no_flames"}
