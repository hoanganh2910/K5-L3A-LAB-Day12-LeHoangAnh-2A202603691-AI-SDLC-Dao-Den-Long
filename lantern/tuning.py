"""Single source of truth for Night 1 numbers and game.contract.json."""

from __future__ import annotations

CONTRACT_VERSION = "1.0"
TEAM = "2A202603691-LeHoangAnh"
BUILD_CMD = "python3 -m pip install -r requirements.txt"
RUN_CMD = "python3 -m lantern play"
HEADLESS_CMD = "python3 -m lantern headless"

PLAYER_SPEED = 6.0
CARRY_CAPACITY = 8
LANTERN_COST = 3
LANTERN_COUNT_NIGHT1 = 5
PICKUP_RADIUS = 1.5
INTERACT_RADIUS = 2.0
PULSE_COST = 1
PULSE_RADIUS = 8.0
NIGHT1_DURATION_S = 180
FLAMES = 3
INVULN_S = 1.0
HIT_DROP_RATIO = 0.0
PULSE_STUN_S = 1.5
PULSE_PUSH_M = 4.0
PULSE_COOLDOWN_S = 0.8
SAFE_RADIUS = 6.0
SHADE_SPEED = 3.5
SHADE_HIT_RADIUS = 1.2
FALL_ENABLED = False

SCORE_PER_MOTE = 10
SCORE_PER_LANTERN = 100
SCORE_PER_STUN = 15
SCORE_PER_SECOND_LEFT = 1
SCORE_PER_FLAME_LEFT = 20

# Not part of the contract. Documented in docs/notes/phase1-assumptions.md.
JUMP_SPEED = 6.5
GRAVITY = -20.0
SHADE_CENTER_Y = 1.0
SPAWN_INTERVAL_S = 20
SHADE_CAP = 4
SPAWN_RADIUS = 28.0
ISLAND_RADIUS = 40.0
PLAY_SEED = 1

# Feet of each pole. The round island is only a visual; the sim is an open XZ plane.
DEFAULT_LANTERNS = (
    ("L1", 0.0, 0.0, 22.0),
    ("L2", 21.0, 0.0, 7.0),
    ("L3", 13.0, 0.0, -18.0),
    ("L4", -13.0, 0.0, -18.0),
    ("L5", -21.0, 0.0, 7.0),
)

# Exactly 15 motes: five lanterns times lantern_cost. Hand-placed, not seed-random.
DEFAULT_MOTES = (
    (0.0, 0.0, 16.0),
    (4.0, 0.0, 20.0),
    (-4.0, 0.0, 19.0),
    (16.0, 0.0, 7.0),
    (18.0, 0.0, 12.0),
    (22.0, 0.0, 2.0),
    (13.0, 0.0, -12.0),
    (8.0, 0.0, -16.0),
    (16.0, 0.0, -16.0),
    (-13.0, 0.0, -12.0),
    (-8.0, 0.0, -16.0),
    (-16.0, 0.0, -15.0),
    (-16.0, 0.0, 7.0),
    (-18.0, 0.0, 12.0),
    (-20.0, 0.0, 2.0),
)

DEFAULT_SHADES = (
    ("S1", 12.0, 0.0, 14.0),
    ("S2", -12.0, 0.0, -8.0),
)


def contract_dict() -> dict:
    return {
        "contract_version": CONTRACT_VERSION,
        "team": TEAM,
        "build_cmd": BUILD_CMD,
        "run_cmd": RUN_CMD,
        "headless_cmd": HEADLESS_CMD,
        "tuning": {
            "player_speed": PLAYER_SPEED,
            "carry_capacity": CARRY_CAPACITY,
            "lantern_cost": LANTERN_COST,
            "lantern_count_night1": LANTERN_COUNT_NIGHT1,
            "pickup_radius": PICKUP_RADIUS,
            "interact_radius": INTERACT_RADIUS,
            "pulse_cost": PULSE_COST,
            "pulse_radius": PULSE_RADIUS,
            "night1_duration_s": NIGHT1_DURATION_S,
            "flames": FLAMES,
            "invuln_s": INVULN_S,
            "hit_drop_ratio": HIT_DROP_RATIO,
            "pulse_stun_s": PULSE_STUN_S,
            "pulse_push_m": PULSE_PUSH_M,
            "pulse_cooldown_s": PULSE_COOLDOWN_S,
            "safe_radius": SAFE_RADIUS,
            "shade_speed": SHADE_SPEED,
            "shade_hit_radius": SHADE_HIT_RADIUS,
            "fall_enabled": FALL_ENABLED,
            "score": {
                "per_mote": SCORE_PER_MOTE,
                "per_lantern": SCORE_PER_LANTERN,
                "per_stun": SCORE_PER_STUN,
                "per_second_left": SCORE_PER_SECOND_LEFT,
                "per_flame_left": SCORE_PER_FLAME_LEFT,
            },
        },
    }
