"""Standard Night 1–3 numbers. game.contract.json is generated from contract_dict()."""

from __future__ import annotations

CONTRACT_VERSION = "1.1"
TEAM = "2A202603691-LeHoangAnh"
BUILD_CMD = "python3 -m pip install -r requirements.txt"
RUN_CMD = "python3 -m lantern play"
HEADLESS_CMD = "python3 -m lantern headless"

PLAYER_SPEED = 6.0
CHARM_SPEED = 7.2
CARRY_CAPACITY = 10
LANTERN_COST = 10
LANTERN_COUNT_NIGHT1 = 5
PICKUP_RADIUS = 1.0
PICKUP_HEIGHT = 1.5
INTERACT_RADIUS = 2.0
PULSE_COST = 3
PULSE_RADIUS = 5.0
PULSE_CENTER_Y = 0.8
NIGHT1_DURATION_S = 300
NIGHT2_DURATION_S = 330
NIGHT3_DURATION_S = 360
FLAMES = 3
INVULN_S = 1.5
HIT_DROP_RATIO = 0.5
PULSE_STUN_S = 2.0
PULSE_PUSH_M = 4.0
PULSE_PUSH_TICKS = 15
PULSE_COOLDOWN_S = 3.0
SAFE_RADIUS = 6.0
SAFE_EJECT_TICKS = 30
SHADE_SPEED = 4.0
SHADE_SPEED_NIGHT3 = 4.5
SHADE_HIT_RADIUS = 1.0
SHADE_HIT_HEIGHT = 1.5
SHADE_DETECT = 12.0
SHADE_LEASH = 18.0
SHADE_RECOIL_M = 2.0
SHADE_RECOIL_TICKS = 60
FALL_ENABLED = True
FALL_Y = -10.0
FALL_WAIT_TICKS = 60

JUMP_SPEED = 7.0
GRAVITY = -20.0
DASH_SPEED = 14.0
DASH_DURATION_S = 0.2
DASH_COOLDOWN_S = 1.5

SCORE_PER_MOTE = 10
SCORE_PER_LANTERN = 100
SCORE_PER_STUN = 5
SCORE_PER_SECOND_LEFT = 2
SCORE_PER_FLAME_LEFT = 50

DROP_TTL_TICKS = 480
DROP_RING_MIN = 1.5
DROP_RING_MAX = 2.5
CHARM_TICKS = 600
CHARM_RESPAWN_TICKS = 2700
DRIFTER_SPEED = 7.0
DRIFTER_IDLE_SPEED = 2.0
DRIFTER_CHASE_RANGE = 15.0
DRIFTER_STEAL_RADIUS = 1.2
DRIFTER_STEAL_MAX = 3
DRIFTER_FLEE_TICKS = 240
DRIFTER_DROP_TICKS = 120
DRIFTER_CARRY_NEED = 5
WIND_PUSH = 2.0
PLAY_SEED = 1

SHADE_CENTER_Y = 1.0
DT = 1.0 / 60.0


def ticks_of(seconds: float) -> int:
    return int(round(seconds * 60))


DASH_TICKS = ticks_of(DASH_DURATION_S)
DASH_COOLDOWN_TICKS = ticks_of(DASH_COOLDOWN_S)
PULSE_COOLDOWN_TICKS = ticks_of(PULSE_COOLDOWN_S)
PULSE_STUN_TICKS = ticks_of(PULSE_STUN_S)
INVULN_TICKS = ticks_of(INVULN_S)


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
            "dash_speed": DASH_SPEED,
            "dash_duration_s": DASH_DURATION_S,
            "dash_cooldown_s": DASH_COOLDOWN_S,
            "night2_duration_s": NIGHT2_DURATION_S,
            "night3_duration_s": NIGHT3_DURATION_S,
        },
    }
