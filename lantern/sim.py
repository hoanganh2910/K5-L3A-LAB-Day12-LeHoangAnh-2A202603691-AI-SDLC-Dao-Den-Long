"""Deterministic 60 Hz Night 1 simulation. No window, no GPU."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from lantern import tuning as T

DT = 1.0 / 60.0
SPAWN_INTERVAL_TICKS = int(T.SPAWN_INTERVAL_S * 60)


def ticks_of(seconds: float) -> int:
    return int(round(seconds * 60))


PULSE_COOLDOWN_TICKS = ticks_of(T.PULSE_COOLDOWN_S)
PULSE_STUN_TICKS = ticks_of(T.PULSE_STUN_S)
INVULN_TICKS = ticks_of(T.INVULN_S)


class FormatError(Exception):
    """Inputs or scenario JSON does not match Test Contract v1.0."""


def r3(value: float) -> float:
    rounded = round(float(value), 3)
    if rounded == 0:
        return 0.0
    return float(rounded)


def xz_dist(ax: float, az: float, bx: float, bz: float) -> float:
    return math.hypot(ax - bx, az - bz)


def id_key(identifier: str) -> tuple:
    index = 0
    while index < len(identifier) and not identifier[index].isdigit():
        index += 1
    prefix = identifier[:index]
    number = int(identifier[index:]) if index < len(identifier) else 0
    return (prefix, number, identifier)


def _is_bool(value: object) -> bool:
    return isinstance(value, bool)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not _is_bool(value) and math.isfinite(float(value))


def _as_int(value: object, label: str) -> int:
    if not _is_number(value):
        raise FormatError(f"{label} must be a number")
    number = float(value)
    if not number.is_integer():
        raise FormatError(f"{label} must be an integer")
    if number < 0:
        raise FormatError(f"{label} must be >= 0")
    return int(number)


def _as_vec3(value: object, label: str) -> tuple[float, float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 3 or any(not _is_number(part) for part in value):
        raise FormatError(f"{label} must be [x, y, z]")
    return (float(value[0]), float(value[1]), float(value[2]))


@dataclass
class Mote:
    id: str
    x: float
    z: float


@dataclass
class Lantern:
    id: str
    x: float
    y: float
    z: float
    deposited: int = 0
    lit: bool = False


@dataclass
class Shade:
    id: str
    x: float
    z: float
    state: str = "chase"
    stun_ticks: int = 0
    just_stunned: bool = False


@dataclass
class Sim:
    seed: int
    duration_s: float
    x: float
    y: float
    z: float
    vx_jump: float
    flames: int
    carried: int
    score: int
    state: str
    steps: int
    motes: list[Mote]
    lanterns: list[Lantern]
    shades: list[Shade]
    spawn_shades: bool
    rng: random.Random
    pulse_cd_ticks: int = 0
    invuln_ticks: int = 0
    move_x: float = 0.0
    move_z: float = 0.0
    yaw: float = 0.0
    prev: dict = field(default_factory=lambda: {"jump": False, "interact": False, "pulse": False})
    edges: dict = field(default_factory=lambda: {"jump": False, "interact": False, "pulse": False})

    @classmethod
    def create(cls, seed: int, scenario: dict | None) -> "Sim":
        config = parse_scenario(scenario)
        lanterns = [
            Lantern(lantern_id, px, py, pz)
            for lantern_id, px, py, pz in T.DEFAULT_LANTERNS
        ]
        by_id = {lantern.id: lantern for lantern in lanterns}
        for spec in config["lanterns"]:
            lantern = by_id[spec["id"]]
            if "pos" in spec:
                lantern.x, lantern.y, lantern.z = spec["pos"]
            if "deposited" in spec:
                lantern.deposited = spec["deposited"]
            if "lit" in spec:
                lantern.lit = spec["lit"]
            elif lantern.deposited >= T.LANTERN_COST:
                lantern.lit = True
        player = config["player"]
        sim = cls(
            seed=seed,
            duration_s=config["time_left_s"],
            x=player["pos"][0],
            y=player["pos"][1],
            z=player["pos"][2],
            vx_jump=0.0,
            flames=player["flames"],
            carried=player["carried"],
            score=0,
            state="playing",
            steps=0,
            motes=[Mote(f"M{index}", mx, mz) for index, (mx, _my, mz) in enumerate(config["motes"], start=1)],
            lanterns=lanterns,
            shades=[],
            spawn_shades=config["spawn_shades"],
            rng=random.Random(seed),
        )
        used_ids: set[str] = set()
        next_number = 1
        for spec in config["shades"]:
            if "id" in spec:
                shade_id = spec["id"]
            else:
                while f"S{next_number}" in used_ids:
                    next_number += 1
                shade_id = f"S{next_number}"
                next_number += 1
            if shade_id in used_ids:
                raise FormatError(f"duplicate shade id {shade_id}")
            used_ids.add(shade_id)
            sim.shades.append(Shade(shade_id, spec["pos"][0], spec["pos"][2]))
        sim._close_if_already_over()
        return sim

    def set_input(self, move: list[float], yaw: float, buttons: dict) -> None:
        self.move_x = float(move[0])
        self.move_z = float(move[1])
        self.yaw = float(yaw)
        for key in ("jump", "interact", "pulse"):
            pressed = bool(buttons.get(key, False))
            self.edges[key] = pressed and not self.prev[key]
            self.prev[key] = pressed

    def step(self) -> list[dict]:
        """Read the input already set for this tick and produce the next state.

        Order is fixed: cooldowns, move, pickup, pulse, deposit, shades, hit, ending.
        Events use tick = steps + 1. Snapshot tick 0 is taken before the first step.
        """
        if self.state != "playing":
            return []
        if self.pulse_cd_ticks > 0:
            self.pulse_cd_ticks -= 1
        if self.invuln_ticks > 0:
            self.invuln_ticks -= 1
        events: list[dict] = []
        self._move()
        events.extend(self._pickups())
        events.extend(self._pulse())
        events.extend(self._interact())
        events.extend(self._update_shades())
        events.extend(self._hits())
        self.steps += 1
        events.extend(self._conclude())
        return events

    def snapshot(self) -> dict:
        remaining = max(0.0, self.duration_s - self.steps / 60.0)
        return {
            "type": "snapshot",
            "tick": self.steps,
            "sim_tick": self.steps,
            "state": self.state,
            "time_left_s": r3(remaining),
            "score": int(self.score),
            "player": {
                "pos": [r3(self.x), r3(self.y), r3(self.z)],
                "flames": int(self.flames),
                "carried": int(self.carried),
            },
            "lanterns": [
                {
                    "id": lantern.id,
                    "pos": [r3(lantern.x), r3(lantern.y), r3(lantern.z)],
                    "lit": bool(lantern.lit),
                    "deposited": int(lantern.deposited),
                }
                for lantern in sorted(self.lanterns, key=lambda lantern: id_key(lantern.id))
            ],
            "shades": [
                {
                    "id": shade.id,
                    "pos": [r3(shade.x), T.SHADE_CENTER_Y, r3(shade.z)],
                    "state": shade.state,
                }
                for shade in sorted(self.shades, key=lambda shade: id_key(shade.id))
            ],
            "motes_active": len(self.motes),
            "motes": [
                {"id": mote.id, "pos": [r3(mote.x), 0.0, r3(mote.z)]}
                for mote in sorted(self.motes, key=lambda mote: id_key(mote.id))
            ],
        }

    def end_record(self) -> dict:
        return {
            "type": "end",
            "ticks": self.steps,
            "state": self.state,
            "score": int(self.score),
        }

    def _event(self, name: str, data: dict) -> dict:
        return {"type": "event", "tick": self.steps + 1, "name": name, "data": data}

    def _close_if_already_over(self) -> None:
        """Setup never emits events and never adds score."""
        if self.flames <= 0:
            self.flames = 0
            self.state = "lost"
        elif self._all_lit():
            self.state = "won"
        elif self.duration_s <= 0:
            self.duration_s = 0
            self.state = "lost"

    def _all_lit(self) -> bool:
        return bool(self.lanterns) and all(lantern.lit for lantern in self.lanterns)

    def _move(self) -> None:
        mx, mz = self.move_x, self.move_z
        length = math.hypot(mx, mz)
        if length > 1:
            mx /= length
            mz /= length
        theta = math.radians(self.yaw)
        world_x = mx * math.cos(theta) + mz * math.sin(theta)
        world_z = -mx * math.sin(theta) + mz * math.cos(theta)
        self.x += world_x * T.PLAYER_SPEED * DT
        self.z += world_z * T.PLAYER_SPEED * DT
        on_ground = self.y <= 1e-8 and self.vx_jump <= 0
        if self.edges["jump"] and on_ground:
            self.vx_jump = T.JUMP_SPEED
        self.vx_jump += T.GRAVITY * DT
        self.y += self.vx_jump * DT
        if self.y <= 0:
            self.y = 0.0
            self.vx_jump = 0.0

    def _pickups(self) -> list[dict]:
        events: list[dict] = []
        kept: list[Mote] = []
        for mote in sorted(self.motes, key=lambda item: id_key(item.id)):
            in_reach = xz_dist(self.x, self.z, mote.x, mote.z) <= T.PICKUP_RADIUS
            if in_reach and self.carried < T.CARRY_CAPACITY:
                self.carried += 1
                self.score += T.SCORE_PER_MOTE
                events.append(self._event("mote_picked", {"carried": self.carried}))
            else:
                kept.append(mote)
        self.motes = kept
        return events

    def _pulse(self) -> list[dict]:
        if not self.edges["pulse"] or self.pulse_cd_ticks > 0 or self.carried < T.PULSE_COST:
            return []
        self.carried -= T.PULSE_COST
        self.pulse_cd_ticks = PULSE_COOLDOWN_TICKS
        stunned_ids: list[str] = []
        for shade in sorted(self.shades, key=lambda item: id_key(item.id)):
            if xz_dist(self.x, self.z, shade.x, shade.z) <= T.PULSE_RADIUS:
                self._push(shade)
                shade.state = "stunned"
                shade.stun_ticks = PULSE_STUN_TICKS
                shade.just_stunned = True
                stunned_ids.append(shade.id)
                self.score += T.SCORE_PER_STUN
        return [self._event("pulse", {"stunned_ids": stunned_ids})]

    def _push(self, shade: Shade) -> None:
        dx = shade.x - self.x
        dz = shade.z - self.z
        dist = math.hypot(dx, dz)
        if dist == 0:
            dx, dz, dist = 1.0, 0.0, 1.0
        shade.x += dx / dist * T.PULSE_PUSH_M
        shade.z += dz / dist * T.PULSE_PUSH_M
        self._clamp_out_of_safe(shade)

    def _interact(self) -> list[dict]:
        if not self.edges["interact"]:
            return []
        candidates: list[tuple] = []
        for lantern in self.lanterns:
            if lantern.lit or lantern.deposited >= T.LANTERN_COST:
                continue
            dist = xz_dist(self.x, self.z, lantern.x, lantern.z)
            if dist <= T.INTERACT_RADIUS:
                candidates.append((dist, id_key(lantern.id), lantern))
        if not candidates:
            return []
        candidates.sort(key=lambda item: (item[0], item[1]))
        lantern = candidates[0][2]
        amount = min(self.carried, T.LANTERN_COST - lantern.deposited)
        if amount <= 0:
            return []
        self.carried -= amount
        lantern.deposited += amount
        events = [
            self._event(
                "deposit",
                {"lantern_id": lantern.id, "amount": amount, "deposited": lantern.deposited},
            )
        ]
        if lantern.deposited >= T.LANTERN_COST:
            lantern.lit = True
            self.score += T.SCORE_PER_LANTERN
            events.append(self._event("lantern_lit", {"lantern_id": lantern.id}))
        return events

    def _update_shades(self) -> list[dict]:
        events: list[dict] = []
        upcoming = self.steps + 1
        if (
            self.spawn_shades
            and upcoming % SPAWN_INTERVAL_TICKS == 0
            and len(self.shades) < T.SHADE_CAP
        ):
            shade = self._spawn_shade()
            events.append(self._event("shade_spawned", {"id": shade.id}))
        for shade in sorted(self.shades, key=lambda item: id_key(item.id)):
            if shade.just_stunned:
                shade.just_stunned = False
                continue
            if shade.stun_ticks > 0:
                shade.stun_ticks -= 1
                shade.state = "stunned"
                if shade.stun_ticks > 0:
                    continue
                shade.state = "chase"
            if shade.state == "chase":
                self._chase(shade)
        return events

    def _spawn_shade(self) -> Shade:
        angle = self.rng.random() * math.tau
        shade = Shade(
            self._next_shade_id(),
            T.SPAWN_RADIUS * math.cos(angle),
            T.SPAWN_RADIUS * math.sin(angle),
        )
        self.shades.append(shade)
        return shade

    def _next_shade_id(self) -> str:
        used = {shade.id for shade in self.shades}
        number = 1
        while f"S{number}" in used:
            number += 1
        return f"S{number}"

    def _chase(self, shade: Shade) -> None:
        dx = self.x - shade.x
        dz = self.z - shade.z
        dist = math.hypot(dx, dz)
        step = T.SHADE_SPEED * DT
        if dist > 1e-9 and step < dist:
            shade.x += dx / dist * step
            shade.z += dz / dist * step
        elif dist > 1e-9:
            shade.x = self.x
            shade.z = self.z
        self._clamp_out_of_safe(shade)

    def _clamp_out_of_safe(self, shade: Shade) -> None:
        if T.SAFE_RADIUS <= 0:
            return
        for lantern in sorted(self.lanterns, key=lambda item: id_key(item.id)):
            if not lantern.lit:
                continue
            dx = shade.x - lantern.x
            dz = shade.z - lantern.z
            dist = math.hypot(dx, dz)
            if dist < T.SAFE_RADIUS:
                if dist == 0:
                    dx, dz, dist = 1.0, 0.0, 1.0
                shade.x = lantern.x + dx / dist * T.SAFE_RADIUS
                shade.z = lantern.z + dz / dist * T.SAFE_RADIUS

    def _hits(self) -> list[dict]:
        if self.invuln_ticks > 0:
            return []
        for shade in sorted(self.shades, key=lambda item: id_key(item.id)):
            if shade.state != "chase":
                continue
            if xz_dist(self.x, self.z, shade.x, shade.z) > T.SHADE_HIT_RADIUS:
                continue
            dropped = min(self.carried, math.floor(self.carried * T.HIT_DROP_RATIO + 1e-9))
            self.carried -= dropped
            self.flames = max(0, self.flames - 1)
            self.invuln_ticks = INVULN_TICKS
            return [
                self._event(
                    "player_hit",
                    {"by": "shade", "flames": int(self.flames), "dropped": int(dropped)},
                )
            ]
        return []

    def _conclude(self) -> list[dict]:
        if self.flames <= 0:
            self.state = "lost"
            return [self._event_over("lost", "no_flames")]
        if self._all_lit():
            self.state = "won"
            remaining = max(0.0, self.duration_s - self.steps / 60.0)
            self.score += math.floor(remaining + 1e-9) * T.SCORE_PER_SECOND_LEFT
            self.score += self.flames * T.SCORE_PER_FLAME_LEFT
            return [self._event_over("won", "all_lit")]
        if self.steps / 60.0 >= self.duration_s - 1e-9:
            self.state = "lost"
            return [self._event_over("lost", "dawn")]
        return []

    def _event_over(self, result: str, reason: str) -> dict:
        # steps was already incremented, so the event tick is the new step count.
        return {
            "type": "event",
            "tick": self.steps,
            "name": "game_over",
            "data": {"result": result, "reason": reason},
        }


def parse_inputs(data: object) -> list[dict]:
    if data is None:
        return []
    if not isinstance(data, dict) or "frames" not in data or not isinstance(data["frames"], list):
        raise FormatError("inputs must be an object with a frames array")
    frames: list[dict] = []
    previous_tick: int | None = None
    for raw in data["frames"]:
        if not isinstance(raw, dict) or "tick" not in raw:
            raise FormatError("each frame needs an integer tick")
        tick = raw["tick"]
        if not isinstance(tick, int) or _is_bool(tick) or tick < 0:
            raise FormatError("frame tick must be an integer >= 0")
        if previous_tick is not None and tick <= previous_tick:
            raise FormatError("frame ticks must strictly increase")
        previous_tick = tick
        frame: dict = {"tick": tick}
        if "move" in raw:
            move = raw["move"]
            if (
                not isinstance(move, (list, tuple))
                or len(move) != 2
                or any(not _is_number(part) for part in move)
            ):
                raise FormatError("move must be [x, z]")
            mx, mz = float(move[0]), float(move[1])
            if mx < -1 or mx > 1 or mz < -1 or mz > 1:
                raise FormatError("move components must be in [-1, 1]")
            frame["move"] = [mx, mz]
        if "cam_yaw_deg" in raw:
            if not _is_number(raw["cam_yaw_deg"]):
                raise FormatError("cam_yaw_deg must be a number")
            frame["cam_yaw_deg"] = float(raw["cam_yaw_deg"])
        for key in ("jump", "interact", "pulse", "dash"):
            if key in raw:
                if not _is_bool(raw[key]):
                    raise FormatError(f"{key} must be a boolean")
                frame[key] = raw[key]
        frames.append(frame)
    return frames


def parse_scenario(data: object) -> dict:
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise FormatError("scenario must be an object")
    player_raw = data.get("player", {})
    if not isinstance(player_raw, dict):
        raise FormatError("player must be an object")
    pos = _as_vec3(player_raw.get("pos", [0, 0, 0]), "player.pos")
    carried = _as_int(player_raw["carried"], "player.carried") if "carried" in player_raw else 0
    flames = _as_int(player_raw["flames"], "player.flames") if "flames" in player_raw else T.FLAMES
    random_motes = _flag(data, "random_motes", True)
    random_shades = _flag(data, "random_shades", True)
    if "motes" in data:
        motes = _parse_motes(data["motes"])
    elif random_motes:
        motes = list(T.DEFAULT_MOTES)
    else:
        motes = []
    if "shades" in data:
        shades = _parse_shades(data["shades"])
    elif random_shades:
        shades = [
            {"id": shade_id, "pos": (sx, sy, sz)}
            for shade_id, sx, sy, sz in T.DEFAULT_SHADES
        ]
    else:
        shades = []
    lanterns = _parse_lanterns(data["lanterns"]) if "lanterns" in data else []
    if "time_left_s" in data:
        if not _is_number(data["time_left_s"]):
            raise FormatError("time_left_s must be a number")
        time_left = float(data["time_left_s"])
        if time_left < 0:
            raise FormatError("time_left_s must be >= 0")
    else:
        time_left = float(T.NIGHT1_DURATION_S)
    return {
        "player": {"pos": pos, "carried": carried, "flames": flames},
        "motes": motes,
        "shades": shades,
        "lanterns": lanterns,
        "spawn_shades": random_shades,
        "time_left_s": time_left,
    }


def _flag(data: dict, key: str, default: bool) -> bool:
    if key not in data:
        return default
    if not _is_bool(data[key]):
        raise FormatError(f"{key} must be a boolean")
    return bool(data[key])


def _parse_motes(value: object) -> list[tuple[float, float, float]]:
    if not isinstance(value, list):
        raise FormatError("motes must be an array")
    return [_as_vec3(item, "mote") for item in value]


def _parse_shades(value: object) -> list[dict]:
    if not isinstance(value, list):
        raise FormatError("shades must be an array")
    shades: list[dict] = []
    for item in value:
        if not isinstance(item, dict) or "pos" not in item:
            raise FormatError("shade must be an object with pos")
        shade = {"pos": _as_vec3(item["pos"], "shade.pos")}
        if "id" in item:
            if not isinstance(item["id"], str) or not item["id"]:
                raise FormatError("shade id must be a non-empty string")
            shade["id"] = item["id"]
        shades.append(shade)
    return shades


def _parse_lanterns(value: object) -> list[dict]:
    if not isinstance(value, list):
        raise FormatError("lanterns must be an array")
    known = {lantern_id for lantern_id, *_rest in T.DEFAULT_LANTERNS}
    lanterns: list[dict] = []
    for item in value:
        if not isinstance(item, dict) or "id" not in item:
            raise FormatError("lantern must be an object with id")
        if item["id"] not in known:
            raise FormatError(f"unknown lantern id {item['id']}")
        spec: dict = {"id": item["id"]}
        if "pos" in item:
            spec["pos"] = _as_vec3(item["pos"], "lantern.pos")
        if "deposited" in item:
            spec["deposited"] = _as_int(item["deposited"], "lantern.deposited")
        if "lit" in item:
            if not _is_bool(item["lit"]):
                raise FormatError("lantern.lit must be a boolean")
            spec["lit"] = item["lit"]
        lanterns.append(spec)
    return lanterns


def run_simulation(
    seed: int,
    scenario: dict | None,
    frames: list[dict],
    n_ticks: int,
    snapshot_every: int,
) -> list[dict]:
    sim = Sim.create(seed, scenario)
    lines = [sim.snapshot()]
    if sim.state != "playing":
        lines.append(sim.end_record())
        return lines
    held_move = [0.0, 0.0]
    held_yaw = 0.0
    held = {"jump": False, "interact": False, "pulse": False, "dash": False}
    by_tick = {frame["tick"]: frame for frame in frames}
    for tick in range(n_ticks):
        frame = by_tick.get(tick)
        if frame:
            if "move" in frame:
                held_move = list(frame["move"])
            if "cam_yaw_deg" in frame:
                held_yaw = frame["cam_yaw_deg"]
            for key in held:
                if key in frame:
                    held[key] = frame[key]
        sim.set_input(held_move, held_yaw, held)
        lines.extend(sim.step())
        if snapshot_every > 0 and sim.steps % snapshot_every == 0:
            lines.append(sim.snapshot())
        if sim.state != "playing":
            break
    lines.append(sim.end_record())
    return lines
