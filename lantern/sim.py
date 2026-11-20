"""Deterministic 60 Hz simulation for Nights 1–3. No window, no GPU."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from lantern import tuning as T
from lantern import world

DT = T.DT


class FormatError(Exception):
    """Inputs or scenario JSON does not match Test Contract v1.1."""


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


SHADE_STATES = {"spawning", "wander", "chase", "recoil", "stunned", "drain"}


def fuel_out(units: int) -> float:
    return round(max(units, 0) / T.FUEL_SUBUNITS, 1)


def fuel_units_from(value: float) -> int:
    return int(round(float(value) * T.FUEL_SUBUNITS))
DRIFTER_STATES = {"idle", "chase", "flee", "removed"}


@dataclass
class Mote:
    id: str
    x: float
    y: float
    z: float
    kind: str = "random"
    ttl: int | None = None


@dataclass
class Lantern:
    id: str
    x: float
    y: float
    z: float
    deposited: int = 0
    lit: bool = False
    fuel_units: int = 0
    ever_lit: bool = False
    relit_count: int = 0


@dataclass
class Shade:
    id: str
    x: float
    z: float
    feet: float = 0.0
    state: str = "chase"
    stun_left: int = 0
    push_left: int = 0
    push_x: float = 1.0
    push_z: float = 0.0
    recoil_left: int = 0
    recoil_x: float = 1.0
    recoil_z: float = 0.0
    eject_left: int = 0
    eject_x: float = 0.0
    eject_z: float = 0.0
    target_id: str | None = None
    drain_ticks: int = 0

    @property
    def y(self) -> float:
        return self.feet + T.SHADE_CENTER_Y


@dataclass
class Drifter:
    id: str
    x: float
    z: float
    state: str = "idle"
    stolen: int = 0
    flee_left: int = 0
    despawn_left: int = 0
    dir_x: float = 1.0
    dir_z: float = 0.0
    y: float = 1.0


@dataclass
class Charm:
    id: str
    x: float
    y: float
    z: float
    available: bool = True
    respawn: int = 0


@dataclass
class Sim:
    seed: int
    night: int
    duration_s: float
    x: float
    y: float
    z: float
    vx: float
    vy: float
    vz: float
    flames: int
    carried: int
    score: int
    state: str
    tick: int
    sim_tick: int
    motes: list[Mote]
    lanterns: list[Lantern]
    shades: list[Shade]
    drifters: list[Drifter]
    charms: list[Charm]
    spawn_motes: bool
    spawn_shades: bool
    spawn_drifters: bool
    wind_enabled: bool
    rng: random.Random
    successful_lights: int = 0
    grounded: bool = True
    face_x: float = 0.0
    face_z: float = 1.0
    dash_left: int = 0
    dash_cd: int = 0
    dash_air: bool = False
    dash_y: float = 0.0
    dash_x: float = 0.0
    dash_z: float = 1.0
    pulse_cd: int = 0
    invuln: int = 0
    charm_left: int = 0
    fall_wait: int = 0
    downed: bool = False
    launch: bool = False
    launch_x: float = 0.0
    launch_z: float = 0.0
    wind_active: bool = False
    wind_dir: float = 0.0
    gust_dir: dict = field(default_factory=dict)
    just_lit: list = field(default_factory=list)
    started: bool = False
    move_x: float = 0.0
    move_z: float = 0.0
    yaw: float = 0.0
    prev: dict = field(default_factory=lambda: {
        "jump": False, "interact": False, "pulse": False, "dash": False, "pause": False
    })
    edges: dict = field(default_factory=lambda: {
        "jump": False, "interact": False, "pulse": False, "dash": False, "pause": False
    })

    @classmethod
    def create(cls, seed: int, scenario: dict | None, night: int = 1) -> "Sim":
        if night not in (1, 2, 3):
            raise FormatError("night must be 1, 2, or 3")
        config = parse_scenario(scenario, night)
        lanterns = [Lantern(lid, px, py, pz) for lid, px, py, pz in world.lantern_specs(night)]
        by_id = {lantern.id: lantern for lantern in lanterns}
        for spec in config["lanterns"]:
            lantern = by_id[spec["id"]]
            if "pos" in spec:
                lantern.x, lantern.y, lantern.z = spec["pos"]
            if "deposited" in spec:
                lantern.deposited = spec["deposited"]
            if spec.get("lit") or lantern.deposited >= T.LANTERN_COST:
                lantern.lit = True
            if "lit" in spec:
                lantern.lit = spec["lit"]
            if lantern.lit and "fuel" not in spec:
                lantern.fuel_units = T.FUEL_MAX_UNITS
            elif "fuel" in spec:
                lantern.fuel_units = fuel_units_from(spec["fuel"])
            if lantern.lit and lantern.fuel_units <= 0 and "fuel" not in spec:
                lantern.fuel_units = T.FUEL_MAX_UNITS
            if "ever_lit" in spec:
                lantern.ever_lit = spec["ever_lit"]
            elif lantern.lit:
                lantern.ever_lit = True
            if not lantern.lit:
                lantern.fuel_units = 0
        player = config["player"]
        sim = cls(
            seed=seed,
            night=night,
            duration_s=config["time_left_s"],
            x=player["pos"][0],
            y=player["pos"][1],
            z=player["pos"][2],
            vx=0.0,
            vy=0.0,
            vz=0.0,
            flames=player["flames"],
            carried=player["carried"],
            score=0,
            state="playing",
            tick=0,
            sim_tick=0,
            motes=[],
            lanterns=lanterns,
            shades=[],
            drifters=[],
            charms=[],
            spawn_motes=config["spawn_motes"],
            spawn_shades=config["spawn_shades"],
            spawn_drifters=config["spawn_drifters"],
            wind_enabled=config["wind_enabled"],
            rng=random.Random(seed),
            dash_cd=player["dash_cd_ticks"],
            pulse_cd=player["pulse_cd_ticks"],
            invuln=player["invuln_ticks"],
            charm_left=player["charm_ticks"],
        )
        for index, (mx, my, mz) in enumerate(config["motes"], start=1):
            sim.motes.append(Mote(f"M{index}", mx, my, mz, "random", None))
        sim._load_shades(config["shades"])
        sim._load_drifters(config["drifters"])
        sim._load_charms(config["charms"])
        sim.grounded = world.support(night, sim.x, sim.z, sim.y, True) is not None and abs(
            sim.y - (world.support(night, sim.x, sim.z, sim.y, True) or sim.y)
        ) <= 0.25
        sim.successful_lights = player["successful_lights"]
        for shade in sim.shades:
            sim._snap_shade_out(shade)
        sim._close_if_already_over()
        return sim

    def set_input(self, move: list[float], yaw: float, buttons: dict) -> None:
        self.move_x = float(move[0])
        self.move_z = float(move[1])
        self.yaw = float(yaw)
        for key in ("jump", "interact", "pulse", "dash", "pause"):
            pressed = bool(buttons.get(key, False))
            self.edges[key] = pressed and not self.prev[key]
            self.prev[key] = pressed

    def step(self) -> list[dict]:
        """One contract step. Events use tick = the wall tick this step produces."""
        if self.edges["pause"] and self.state == "playing":
            self.state = "paused"
            event = self._event("paused", {})
            self.tick += 1
            return [event]
        resumed = None
        if self.state == "paused":
            if self.edges["pause"]:
                self.state = "playing"
                resumed = self._event("resumed", {})
            else:
                self.tick += 1
                return []
        elif self.state != "playing":
            return []

        events: list[dict] = []
        if resumed is not None:
            events.append(resumed)
        if not self.started:
            events.append(self._event("night_start", {"night": self.night}))
            self.started = True
        events.extend(self._decay())
        if self.fall_wait > 0:
            self._live_world(events, frozen=True)
        else:
            self._dash_started = False
            self._move()
            if self._dash_started:
                events.append(self._event("dash", {}))
            if not self.downed:
                events.extend(self._pickups())
                events.extend(self._interact())
                self._safe_zones()
                events.extend(self._pulse())
            self._live_world(events, frozen=self.downed)
        upcoming = self.sim_tick + 1
        events.extend(self._spawns(upcoming))
        events.extend(self._conclude(upcoming))
        self.sim_tick = upcoming
        self.tick += 1
        return events

    def snapshot(self) -> dict:
        remaining = max(0.0, self.duration_s - self.sim_tick / 60.0)
        return {
            "type": "snapshot",
            "tick": self.tick,
            "sim_tick": self.sim_tick,
            "state": self.state,
            "time_left_s": r3(remaining),
            "score": int(self.score),
            "night": self.night,
            "wind": {"active": bool(self.wind_active), "dir_deg": r3(self.wind_dir)},
            "player": {
                "pos": [r3(self.x), r3(self.y), r3(self.z)],
                "vel": [r3(self.vx), r3(self.vy), r3(self.vz)],
                "flames": int(self.flames),
                "carried": int(self.carried),
                "capacity": int(self.carry_cap()),
                "grounded": bool(self.grounded),
                "invuln": r3(self.invuln / 60.0),
                "dash_cd_s": r3(self.dash_cd / 60.0),
                "pulse_cd_s": r3(self.pulse_cd / 60.0),
                "charm_s": r3(self.charm_left / 60.0),
            },
            "lanterns": [
                {
                    "id": lantern.id,
                    "pos": [r3(lantern.x), r3(lantern.y), r3(lantern.z)],
                    "lit": bool(lantern.lit),
                    "deposited": int(lantern.deposited),
                    "fuel": fuel_out(lantern.fuel_units if lantern.lit else 0),
                    "ever_lit": bool(lantern.ever_lit),
                    "relit_count": int(lantern.relit_count),
                }
                for lantern in sorted(self.lanterns, key=lambda lantern: id_key(lantern.id))
            ],
            "shades": [
                {
                    "id": shade.id,
                    "pos": [r3(shade.x), r3(shade.y), r3(shade.z)],
                    "state": shade.state,
                }
                for shade in sorted(self.shades, key=lambda shade: id_key(shade.id))
            ],
            "motes_active": len(self.motes),
            "motes": [
                {
                    "id": mote.id,
                    "pos": [r3(mote.x), r3(mote.y), r3(mote.z)],
                    "kind": mote.kind,
                    "ttl_s": None if mote.ttl is None else r3(max(mote.ttl, 0) / 60.0),
                }
                for mote in sorted(self.motes, key=lambda mote: id_key(mote.id))
            ],
            "drifters": [
                {
                    "id": drifter.id,
                    "pos": [r3(drifter.x), r3(drifter.y), r3(drifter.z)],
                    "state": drifter.state,
                    "stolen": int(drifter.stolen),
                }
                for drifter in sorted(self.drifters, key=lambda item: id_key(item.id))
                if drifter.state != "removed"
            ],
            "charms": [
                {
                    "id": charm.id,
                    "available": bool(charm.available),
                    "respawn_s": r3(0.0 if charm.available else charm.respawn / 60.0),
                }
                for charm in sorted(self.charms, key=lambda item: id_key(item.id))
            ],
        }

    def end_record(self) -> dict:
        return {"type": "end", "ticks": self.tick, "state": self.state, "score": int(self.score)}

    def _event(self, name: str, data: dict) -> dict:
        return {"type": "event", "tick": self.tick + 1, "name": name, "data": data}

    def carry_cap(self) -> int:
        return min(T.CAPACITY_MAX, T.CARRY_CAPACITY + 2 * self.successful_lights)

    def _lit_count(self) -> int:
        return sum(1 for lantern in self.lanterns if lantern.lit)

    def _win_need(self) -> int:
        count = len(self.lanterns)
        return (count * 3 + 4) // 5

    def _close_if_already_over(self) -> None:
        if self.flames <= 0:
            self.flames = 0
            self.state = "lost"
        elif self.duration_s <= 0:
            self.duration_s = 0
            self.state = "won" if self._lit_count() >= self._win_need() else "lost"

    def _decay(self) -> list[dict]:
        if self.dash_cd > 0:
            self.dash_cd -= 1
        if self.dash_left > 0:
            self.dash_left -= 1
        if self.pulse_cd > 0:
            self.pulse_cd -= 1
        if self.invuln > 0:
            self.invuln -= 1
        if self.charm_left > 0:
            self.charm_left -= 1
        if self.fall_wait > 0:
            self.fall_wait -= 1
            if self.fall_wait == 0:
                self._respawn()
        for shade in self.shades:
            if shade.stun_left > 0:
                shade.stun_left -= 1
                if shade.stun_left == 0 and shade.state == "stunned":
                    shade.state = "wander"
            if shade.push_left > 0:
                shade.push_left -= 1
            if shade.recoil_left > 0:
                shade.recoil_left -= 1
                if shade.recoil_left == 0 and shade.state == "recoil":
                    shade.state = "wander"
            if shade.eject_left > 0:
                shade.eject_left -= 1
        for mote in list(self.motes):
            if mote.ttl is None:
                continue
            mote.ttl -= 1
        self.motes = [mote for mote in self.motes if mote.ttl is None or mote.ttl >= 0]
        for charm in self.charms:
            if not charm.available and charm.respawn > 0:
                charm.respawn -= 1
                if charm.respawn == 0:
                    charm.available = True
        for drifter in list(self.drifters):
            if drifter.despawn_left > 0:
                drifter.despawn_left -= 1
                if drifter.despawn_left == 0:
                    drifter.state = "removed"
            elif drifter.flee_left > 0:
                drifter.flee_left -= 1
                if drifter.flee_left == 0:
                    drifter.state = "removed"
        self.drifters = [drifter for drifter in self.drifters if drifter.state != "removed"]
        phase, index = world.gust_phase(self.sim_tick + 1)
        if self.wind_enabled and phase in ("warn", "active") and index not in self.gust_dir:
            self.gust_dir[index] = self.rng.random() * 360.0
        if self.wind_enabled and phase == "active":
            self.wind_active = True
            self.wind_dir = self.gust_dir.get(index, 0.0)
        elif self.wind_enabled and phase == "warn":
            self.wind_active = False
            self.wind_dir = self.gust_dir.get(index, 0.0)
        else:
            self.wind_active = False
            self.wind_dir = 0.0
        return self._burn_fuel()

    def _burn_fuel(self) -> list[dict]:
        events = []
        for lantern in self.lanterns:
            if not lantern.lit:
                continue
            lantern.fuel_units -= 1
            for shade in sorted(self.shades, key=lambda item: id_key(item.id)):
                if shade.state != "drain" or shade.target_id != lantern.id:
                    continue
                lantern.fuel_units -= 5
                if lantern.fuel_units < 0:
                    lantern.fuel_units = 0
                shade.drain_ticks += 1
                if shade.drain_ticks % 60 == 0:
                    events.append(
                        self._event(
                            "fuel_drain",
                            {"lantern_id": lantern.id, "shade_id": shade.id, "fuel": fuel_out(lantern.fuel_units)},
                        )
                    )
            if lantern.fuel_units <= 0:
                lantern.fuel_units = 0
                lantern.lit = False
                lantern.deposited = 0
                lantern.ever_lit = True
                events.append(self._event("lantern_out", {"lantern_id": lantern.id}))
                for shade in self.shades:
                    if shade.state == "drain" and shade.target_id == lantern.id:
                        shade.state = "wander"
                        shade.target_id = None
        return events

    def _respawn(self) -> None:
        self.x, self.y, self.z = 0.0, 0.0, 0.0
        self.vx = self.vy = self.vz = 0.0
        self.grounded = True
        self.downed = False
        self.launch = False
        self.dash_left = 0
        self.invuln = T.INVULN_TICKS
        self.face_x, self.face_z = 0.0, 1.0

    def _wish(self) -> tuple[float, float]:
        mx, mz = self.move_x, self.move_z
        length = math.hypot(mx, mz)
        if length > 1:
            mx /= length
            mz /= length
        theta = math.radians(self.yaw)
        world_x = mx * math.cos(theta) + mz * math.sin(theta)
        world_z = -mx * math.sin(theta) + mz * math.cos(theta)
        return world_x, world_z

    def _move(self) -> None:
        wish_x, wish_z = self._wish()
        moving = math.hypot(wish_x, wish_z) > 1e-8
        if moving:
            self.face_x, self.face_z = wish_x, wish_z
        if self.edges["dash"] and self.dash_left == 0 and (self.dash_cd == 0 or self.charm_left > 0):
            if moving:
                self.dash_x, self.dash_z = wish_x, wish_z
            elif self.launch and math.hypot(self.launch_x, self.launch_z) > 0:
                length = math.hypot(self.launch_x, self.launch_z)
                self.dash_x, self.dash_z = self.launch_x / length, self.launch_z / length
            elif math.hypot(self.vx, self.vz) > 0.1:
                length = math.hypot(self.vx, self.vz)
                self.dash_x, self.dash_z = self.vx / length, self.vz / length
            else:
                self.dash_x, self.dash_z = self.face_x, self.face_z
            length = math.hypot(self.dash_x, self.dash_z) or 1.0
            self.dash_x /= length
            self.dash_z /= length
            self.dash_left = T.DASH_TICKS
            self.dash_air = not self.grounded
            self.dash_y = self.y
            self._dash_started = True
            if self.charm_left == 0:
                self.dash_cd = T.DASH_COOLDOWN_TICKS
            else:
                self.dash_cd = 0
        speed = T.CHARM_SPEED if self.charm_left > 0 else T.PLAYER_SPEED
        if self.dash_left > 0:
            self.vx = self.dash_x * T.DASH_SPEED
            self.vz = self.dash_z * T.DASH_SPEED
            self.vy = 0.0
            self._slide(self.vx * DT, self.vz * DT)
            if self.dash_air:
                self.y = self.dash_y
                self.grounded = False
            else:
                self._land()
            return
        if self.launch and not self.grounded:
            self.vx, self.vz = self.launch_x, self.launch_z
        else:
            self.vx = wish_x * speed
            self.vz = wish_z * speed
        if self.wind_active and not self.launch:
            rad = math.radians(self.wind_dir)
            self.vx += T.WIND_PUSH * math.cos(rad)
            self.vz += T.WIND_PUSH * math.sin(rad)
        if self.edges["jump"] and self.grounded:
            self.vy = T.JUMP_SPEED
            self.grounded = False
            self.launch = False
        if not self.grounded:
            self.vy += T.GRAVITY * DT
            self.y += self.vy * DT
        self._slide(self.vx * DT, self.vz * DT)
        self._land()
        self._pads()
        if T.FALL_ENABLED and self.y < T.FALL_Y and not self.downed:
            self._fall()

    def _slide(self, dx: float, dz: float) -> None:
        next_x = self.x + dx
        next_z = self.z + dz
        if world.inside_bell(self.night, next_x, next_z, self.y):
            return
        self.x, self.z = next_x, next_z

    def _land(self) -> None:
        floor = world.support(self.night, self.x, self.z, self.y, self.grounded or self.y <= 0.02)
        if floor is None:
            self.grounded = False
            self.launch = self.launch and self.y > T.FALL_Y
            return
        if self.y <= floor + 0.02 or (self.grounded and floor <= self.y + 0.25):
            self.y = floor
            self.vy = 0.0
            self.grounded = True
            self.launch = False
        else:
            self.grounded = False

    def _pads(self) -> None:
        if not self.grounded:
            return
        for pad in world.pads(self.night):
            if xz_dist(self.x, self.z, pad["x"], pad["z"]) <= 1.0 and abs(self.y - pad["y"]) <= 0.2:
                self.launch = True
                self.launch_x = pad["vx"]
                self.launch_z = pad["vz"]
                self.vy = pad["vy"]
                self.vx = pad["vx"]
                self.vz = pad["vz"]
                self.grounded = False
                self.y = pad["y"] + 0.05
                return

    def _fall(self) -> None:
        lost = self.carried
        self.carried = 0
        self.flames = max(0, self.flames - 1)
        self.y = T.FALL_Y
        self.vx = self.vy = self.vz = 0.0
        self.grounded = False
        self.launch = False
        self._pending_fall = {"flames": int(self.flames), "lost": int(lost)}
        self.downed = True
        self.fall_wait = 0 if self.flames <= 0 else T.FALL_WAIT_TICKS

    def _pickups(self) -> list[dict]:
        events: list[dict] = []
        kept: list[Mote] = []
        for mote in sorted(self.motes, key=lambda item: id_key(item.id)):
            close = xz_dist(self.x, self.z, mote.x, mote.z) <= T.PICKUP_RADIUS
            low = abs(self.y - mote.y) <= T.PICKUP_HEIGHT
            if close and low and self.carried < self.carry_cap() and (mote.ttl is None or mote.ttl >= 0):
                self.carried += 1
                events.append(self._event("mote_picked", {"carried": self.carried}))
            else:
                kept.append(mote)
        self.motes = kept
        for charm in sorted(self.charms, key=lambda item: (xz_dist(self.x, self.z, item.x, item.z), id_key(item.id))):
            if not charm.available:
                continue
            if xz_dist(self.x, self.z, charm.x, charm.z) > T.PICKUP_RADIUS:
                continue
            if abs(self.y - charm.y) > T.PICKUP_HEIGHT:
                continue
            charm.available = False
            charm.respawn = T.CHARM_RESPAWN_TICKS
            self.charm_left = T.CHARM_TICKS
            self.dash_cd = 0
            events.append(self._event("charm_picked", {"charm_id": charm.id, "charm_ticks": T.CHARM_TICKS}))
            break
        return events

    def _light_cost(self, lantern: Lantern) -> int:
        return T.RELIGHT_COST if lantern.ever_lit else T.LANTERN_COST

    def _needs_oil(self, lantern: Lantern) -> bool:
        if lantern.lit:
            return lantern.fuel_units < T.FUEL_MAX_UNITS
        return lantern.deposited < self._light_cost(lantern)

    def _crosses_safe(self, lantern: Lantern, was_safe: bool) -> None:
        if lantern.lit and lantern.fuel_units >= T.LOW_FUEL_UNITS and not was_safe:
            self.just_lit.append(lantern)

    def _interact(self) -> list[dict]:
        if not self.edges["interact"]:
            return []
        candidates = []
        for lantern in self.lanterns:
            if not self._needs_oil(lantern):
                continue
            dist = xz_dist(self.x, self.z, lantern.x, lantern.z)
            if dist <= T.INTERACT_RADIUS:
                candidates.append((dist, id_key(lantern.id), lantern))
        if not candidates or self.carried <= 0:
            return []
        candidates.sort(key=lambda item: (item[0], item[1]))
        lantern = candidates[0][2]
        was_safe = lantern.lit and lantern.fuel_units >= T.LOW_FUEL_UNITS
        if lantern.lit:
            gap = T.FUEL_MAX_UNITS - lantern.fuel_units
            mote_units = T.FUEL_PER_MOTE * T.FUEL_SUBUNITS
            used = min(self.carried, (gap + mote_units - 1) // mote_units)
            if used <= 0:
                return []
            self.carried -= used
            lantern.fuel_units = min(T.FUEL_MAX_UNITS, lantern.fuel_units + used * mote_units)
            self.score += used * T.SCORE_PER_MOTE
            self._crosses_safe(lantern, was_safe)
            return [self._event("refuel", {"lantern_id": lantern.id, "amount": used, "fuel": fuel_out(lantern.fuel_units)})]
        cost = self._light_cost(lantern)
        amount = min(self.carried, cost - lantern.deposited)
        if amount <= 0:
            return []
        self.carried -= amount
        lantern.deposited += amount
        self.score += amount * T.SCORE_PER_MOTE
        events = [self._event("deposit", {"lantern_id": lantern.id, "amount": amount, "deposited": lantern.deposited})]
        if lantern.deposited >= cost:
            relight = lantern.ever_lit
            lantern.lit = True
            lantern.fuel_units = T.FUEL_MAX_UNITS
            lantern.ever_lit = True
            self.successful_lights += 1
            if relight:
                lantern.relit_count += 1
                self.score += T.SCORE_RELIGHT
            else:
                self.score += T.SCORE_PER_LANTERN
            self._crosses_safe(lantern, was_safe)
            events.append(self._event("lantern_lit", {"lantern_id": lantern.id, "relight": relight}))
        return events

    def _safe_zones(self) -> None:
        for lantern in self.just_lit:
            for shade in self.shades:
                if xz_dist(shade.x, shade.z, lantern.x, lantern.z) < T.SAFE_RADIUS:
                    shade.eject_left = T.SAFE_EJECT_TICKS
                    shade.eject_x = lantern.x
                    shade.eject_z = lantern.z
        self.just_lit = []

    def _pulse(self) -> list[dict]:
        if not self.edges["pulse"] or self.pulse_cd > 0 or self.carried < T.PULSE_COST:
            return []
        self.carried -= T.PULSE_COST
        self.pulse_cd = T.PULSE_COOLDOWN_TICKS
        center_y = self.y + T.PULSE_CENTER_Y
        stunned: list[str] = []
        for shade in sorted(self.shades, key=lambda item: id_key(item.id)):
            dist = math.dist((self.x, center_y, self.z), (shade.x, shade.y, shade.z))
            if dist > T.PULSE_RADIUS:
                continue
            draining = shade.state == "drain"
            self._arm_push(shade)
            shade.state = "stunned"
            shade.stun_left = T.PULSE_STUN_TICKS
            shade.recoil_left = 0
            shade.target_id = None
            stunned.append(shade.id)
            self.score += T.SCORE_DRAIN_STUN if draining else T.SCORE_PER_STUN
        events = [self._event("pulse", {"stunned_ids": stunned})]
        for drifter in sorted(self.drifters, key=lambda item: id_key(item.id)):
            dist = math.dist((self.x, center_y, self.z), (drifter.x, drifter.y, drifter.z))
            if dist > T.PULSE_RADIUS:
                continue
            if drifter.state == "chase":
                self._flee(drifter, steal=False)
            elif drifter.state == "flee" and drifter.stolen > 0:
                events.append(self._drop_stolen(drifter))
        return events

    def _arm_push(self, shade: Shade) -> None:
        dx = shade.x - self.x
        dz = shade.z - self.z
        dist = math.hypot(dx, dz)
        if dist == 0:
            dx, dz, dist = 1.0, 0.0, 1.0
        shade.push_x = dx / dist
        shade.push_z = dz / dist
        shade.push_left = T.PULSE_PUSH_TICKS

    def _flee(self, drifter: Drifter, steal: bool) -> None:
        dx = drifter.x - self.x
        dz = drifter.z - self.z
        dist = math.hypot(dx, dz)
        if dist == 0:
            dx, dz, dist = 1.0, 0.0, 1.0
        drifter.dir_x = dx / dist
        drifter.dir_z = dz / dist
        drifter.state = "flee"
        drifter.flee_left = T.DRIFTER_FLEE_TICKS
        drifter.despawn_left = 0

    def _drop_stolen(self, drifter: Drifter) -> dict:
        amount = drifter.stolen
        for _ in range(amount):
            self.motes.append(
                Mote(self._next_id("M", self.motes), drifter.x, drifter.y - 1.0, drifter.z, "dropped", T.DROP_TTL_TICKS)
            )
        drifter.stolen = 0
        drifter.flee_left = 0
        drifter.despawn_left = T.DRIFTER_DROP_TICKS
        drifter.state = "flee"
        return self._event("drifter_drop", {"drifter_id": drifter.id, "amount": amount})

    def _live_world(self, events: list[dict], frozen: bool) -> None:
        pending = getattr(self, "_pending_fall", None)
        if pending is not None:
            events.append(self._event("player_hit", {"by": "fall", "flames": pending["flames"], "dropped": 0, "lost": pending["lost"]}))
            self._pending_fall = None
        self._move_shades()
        if not frozen:
            self._move_drifters()
            events.extend(self._touch(events))

    def _move_shades(self) -> None:
        speed = world.shade_speed(self.night) * DT
        for shade in sorted(self.shades, key=lambda item: id_key(item.id)):
            if shade.state == "spawning":
                shade.state = "wander"
            if shade.eject_left > 0:
                if shade.state == "drain":
                    shade.state = "wander"
                    shade.target_id = None
                self._eject(shade)
                continue
            if shade.state == "stunned":
                if shade.push_left > 0:
                    self._nudge(shade, shade.push_x, shade.push_z, T.PULSE_PUSH_M / T.PULSE_PUSH_TICKS)
                continue
            if shade.state == "recoil":
                self._nudge(shade, shade.recoil_x, shade.recoil_z, T.SHADE_RECOIL_M / T.SHADE_RECOIL_TICKS)
                continue
            if shade.state == "drain":
                self._update_drain(shade)
                continue
            dist = xz_dist(shade.x, shade.z, self.x, self.z)
            if shade.state == "chase" and dist > T.SHADE_LEASH:
                shade.state = "wander"
            elif shade.state == "wander" and dist <= T.SHADE_DETECT:
                shade.state = "chase"
            if shade.state == "chase":
                self._step_toward(shade, self.x, self.z, speed)
            elif shade.state == "wander":
                self._wander(shade, speed)
            self._block_safe(shade)

    def _update_drain(self, shade: Shade) -> None:
        lantern = self._lantern_by_id(shade.target_id)
        dist = 999.0 if lantern is None else xz_dist(shade.x, shade.z, lantern.x, lantern.z)
        if (
            lantern is None
            or not lantern.lit
            or lantern.fuel_units >= T.LOW_FUEL_UNITS
            or dist > 2.0
        ):
            shade.state = "wander"
            shade.target_id = None
            return
        if xz_dist(shade.x, shade.z, self.x, self.z) <= T.SAFE_RADIUS:
            shade.state = "chase"

    def _wander(self, shade: Shade, speed: float) -> None:
        target = self._pick_lantern(shade)
        if target is None:
            shade.target_id = None
            return
        shade.target_id = target.id
        dist = xz_dist(shade.x, shade.z, target.x, target.z)
        if target.lit and target.fuel_units < T.LOW_FUEL_UNITS and dist <= 2.0:
            shade.state = "drain"
            shade.drain_ticks = 0
            return
        self._step_toward(shade, target.x, target.z, speed)

    def _pick_lantern(self, shade: Shade) -> Lantern | None:
        weak = [lantern for lantern in self.lanterns if lantern.lit and lantern.fuel_units < T.LOW_FUEL_UNITS]
        pool = weak if weak else [lantern for lantern in self.lanterns if not lantern.lit]
        if not pool:
            return None
        pool.sort(key=lambda lantern: (xz_dist(shade.x, shade.z, lantern.x, lantern.z), id_key(lantern.id)))
        return pool[0]

    def _lantern_by_id(self, lantern_id: str | None) -> Lantern | None:
        if lantern_id is None:
            return None
        for lantern in self.lanterns:
            if lantern.id == lantern_id:
                return lantern
        return None

    def _eject(self, shade: Shade) -> None:
        dx = shade.x - shade.eject_x
        dz = shade.z - shade.eject_z
        dist = math.hypot(dx, dz)
        if dist == 0:
            dx, dz, dist = 1.0, 0.0, 1.0
        target_x = shade.eject_x + dx / dist * T.SAFE_RADIUS
        target_z = shade.eject_z + dz / dist * T.SAFE_RADIUS
        shade.x += (target_x - shade.x) / shade.eject_left
        shade.z += (target_z - shade.z) / shade.eject_left
        self._plant(shade)

    def _nudge(self, shade: Shade, dx: float, dz: float, distance: float) -> None:
        next_x = shade.x + dx * distance
        next_z = shade.z + dz * distance
        if not world.surfaces(self.night, next_x, next_z):
            shade.push_left = 0
            return
        shade.x, shade.z = next_x, next_z
        self._plant(shade)

    def _step_toward(self, shade: Shade, tx: float, tz: float, step: float) -> None:
        dx = tx - shade.x
        dz = tz - shade.z
        dist = math.hypot(dx, dz)
        if dist < 1e-9:
            return
        move = min(step, dist)
        next_x = shade.x + dx / dist * move
        next_z = shade.z + dz / dist * move
        if not world.surfaces(self.night, next_x, next_z):
            return
        shade.x, shade.z = next_x, next_z
        self._plant(shade)

    def _plant(self, shade: Shade) -> None:
        floor = world.support(self.night, shade.x, shade.z, shade.feet, True)
        if floor is None:
            floor = 0.0
        shade.feet = floor

    def _block_safe(self, shade: Shade) -> None:
        if shade.eject_left > 0:
            return
        for lantern in sorted(self.lanterns, key=lambda item: id_key(item.id)):
            if not lantern.lit or lantern.fuel_units < T.LOW_FUEL_UNITS:
                continue
            dx = shade.x - lantern.x
            dz = shade.z - lantern.z
            dist = math.hypot(dx, dz)
            if dist < T.SAFE_RADIUS:
                if dist == 0:
                    dx, dz, dist = 1.0, 0.0, 1.0
                shade.x = lantern.x + dx / dist * T.SAFE_RADIUS
                shade.z = lantern.z + dz / dist * T.SAFE_RADIUS
                self._plant(shade)

    def _snap_shade_out(self, shade: Shade) -> None:
        self._block_safe(shade)

    def _move_drifters(self) -> None:
        for drifter in sorted(self.drifters, key=lambda item: id_key(item.id)):
            if drifter.despawn_left > 0:
                continue
            dist = xz_dist(drifter.x, drifter.z, self.x, self.z)
            if drifter.state == "chase" and (self.carried < T.DRIFTER_CARRY_NEED or dist > T.DRIFTER_CHASE_RANGE):
                drifter.state = "idle"
            elif drifter.state == "idle" and self.carried >= T.DRIFTER_CARRY_NEED and dist <= T.DRIFTER_CHASE_RANGE:
                drifter.state = "chase"
            if drifter.state == "chase":
                self._drift(drifter, self.x - drifter.x, self.z - drifter.z, T.DRIFTER_SPEED)
            elif drifter.state == "flee":
                self._drift(drifter, drifter.dir_x, drifter.dir_z, T.DRIFTER_SPEED)
            else:
                self._drift(drifter, drifter.dir_x, drifter.dir_z, T.DRIFTER_IDLE_SPEED)

    def _drift(self, drifter: Drifter, dx: float, dz: float, speed: float) -> None:
        dist = math.hypot(dx, dz)
        if dist < 1e-9:
            dx, dz, dist = drifter.dir_x, drifter.dir_z, 1.0
        step = speed * DT
        next_x = drifter.x + dx / dist * step
        next_z = drifter.z + dz / dist * step
        if not world.surfaces(self.night, next_x, next_z):
            drifter.dir_x *= -1
            drifter.dir_z *= -1
            return
        drifter.x, drifter.z = next_x, next_z
        drifter.dir_x, drifter.dir_z = dx / dist, dz / dist

    def _touch(self, events: list[dict]) -> list[dict]:
        found: list[dict] = []
        for drifter in sorted(self.drifters, key=lambda item: id_key(item.id)):
            if drifter.state != "chase" or drifter.stolen > 0:
                continue
            if xz_dist(self.x, self.z, drifter.x, drifter.z) > T.DRIFTER_STEAL_RADIUS:
                continue
            amount = min(T.DRIFTER_STEAL_MAX, self.carried)
            if amount <= 0:
                continue
            self.carried -= amount
            drifter.stolen = amount
            self._flee(drifter, steal=True)
            found.append(self._event("drifter_steal", {"drifter_id": drifter.id, "amount": amount, "carried": self.carried}))
        if self.invuln > 0 or self.downed:
            return found
        for shade in sorted(self.shades, key=lambda item: id_key(item.id)):
            if shade.state != "chase" or shade.eject_left > 0:
                continue
            if xz_dist(self.x, self.z, shade.x, shade.z) > T.SHADE_HIT_RADIUS:
                continue
            if abs(self.y - shade.feet) > T.SHADE_HIT_HEIGHT:
                continue
            dropped = self.carried // 2
            self._scatter(dropped)
            self.carried -= dropped
            self.flames = max(0, self.flames - 1)
            self.invuln = T.INVULN_TICKS
            dx = shade.x - self.x
            dz = shade.z - self.z
            dist = math.hypot(dx, dz)
            if dist == 0:
                dx, dz = 1.0, 0.0
                dist = 1.0
            shade.recoil_x = dx / dist
            shade.recoil_z = dz / dist
            shade.recoil_left = T.SHADE_RECOIL_TICKS
            shade.state = "recoil"
            shade.stun_left = 0
            self._nudge(shade, shade.recoil_x, shade.recoil_z, T.SHADE_RECOIL_M / T.SHADE_RECOIL_TICKS)
            found.append(self._event("player_hit", {"by": "shade", "flames": int(self.flames), "dropped": int(dropped)}))
            break
        return found

    def _scatter(self, count: int) -> None:
        for _ in range(count):
            angle = self.rng.random() * math.tau
            radius = T.DROP_RING_MIN + self.rng.random() * (T.DROP_RING_MAX - T.DROP_RING_MIN)
            mx = self.x + math.cos(angle) * radius
            mz = self.z + math.sin(angle) * radius
            floors = world.surfaces(self.night, mx, mz)
            my = min(floors) if floors else 0.0
            self.motes.append(Mote(self._next_id("M", self.motes), mx, my, mz, "dropped", T.DROP_TTL_TICKS))

    def _spawns(self, upcoming: int) -> list[dict]:
        events: list[dict] = []
        if self.spawn_motes and upcoming % 240 == 0 and len(self.motes) < 30:
            empty = self._empty_mote_points()
            if empty:
                pick = empty[self.rng.randrange(len(empty))]
                self.motes.append(Mote(self._next_id("M", self.motes), pick[0], pick[1], pick[2], "random", None))
        if self.spawn_shades:
            wanted = _shade_spawn_count(self.night, upcoming)
            if wanted and len(self.shades) + wanted <= world.shade_cap(self.night):
                valid = [
                    point for point in world.shade_points(self.night)
                    if xz_dist(point[0], point[2], self.x, self.z) >= 15.0
                ]
                if len(valid) >= wanted:
                    for _ in range(wanted):
                        point = valid.pop(self.rng.randrange(len(valid)))
                        shade = Shade(self._next_id("S", self.shades), point[0], point[2], state="spawning")
                        self.shades.append(shade)
                        events.append(self._event("shade_spawned", {"id": shade.id}))
        if self.spawn_drifters and self.night >= 2 and upcoming % 1200 == 0 and len(self.drifters) < 2:
            dew = [
                point for point in world.dew_points(self.night)
                if xz_dist(point[0], point[2], self.x, self.z) >= 8.0
            ]
            if dew:
                point = dew[self.rng.randrange(len(dew))]
                angle = self.rng.random() * math.tau
                drifter = Drifter(
                    self._next_id("D", self.drifters),
                    point[0],
                    point[2],
                    "idle",
                    0,
                    0,
                    0,
                    math.cos(angle),
                    math.sin(angle),
                )
                self.drifters.append(drifter)
        return events

    def _empty_mote_points(self) -> list[tuple[float, float, float]]:
        empty = []
        for point in world.mote_points(self.night):
            if all(xz_dist(point[0], point[2], mote.x, mote.z) > 0.5 for mote in self.motes):
                empty.append(point)
        return empty

    def _conclude(self, upcoming: int) -> list[dict]:
        if self.flames <= 0:
            self.state = "lost"
            return [self._over("lost", "no_flames")]
        if upcoming >= int(round(self.duration_s * 60)):
            if self._lit_count() >= self._win_need():
                self.state = "won"
                for lantern in self.lanterns:
                    if lantern.lit:
                        self.score += T.SCORE_DAWN_LANTERN + lantern.fuel_units // T.FUEL_SUBUNITS
                self.score += self.flames * T.SCORE_PER_FLAME_LEFT
                return [self._over("won", "dawn_survived")]
            self.state = "lost"
            return [self._over("lost", "dawn")]
        return []

    def _over(self, result: str, reason: str) -> dict:
        return {"type": "event", "tick": self.tick + 1, "name": "game_over", "data": {"result": result, "reason": reason}}

    def _next_id(self, prefix: str, items) -> str:
        used = {item.id for item in items}
        number = 1
        while f"{prefix}{number}" in used:
            number += 1
        return f"{prefix}{number}"

    def _load_shades(self, specs: list[dict]) -> None:
        used: set[str] = set()
        number = 1
        for spec in specs:
            if "id" in spec:
                shade_id = spec["id"]
            else:
                while f"S{number}" in used:
                    number += 1
                shade_id = f"S{number}"
                number += 1
            if shade_id in used:
                raise FormatError(f"duplicate shade id {shade_id}")
            used.add(shade_id)
            shade = Shade(
                shade_id,
                spec["pos"][0],
                spec["pos"][2],
                feet=spec["pos"][1],
                state=spec.get("state", "chase"),
                target_id=spec.get("target_lantern_id"),
            )
            ticks = spec.get("state_ticks_left", 0)
            if shade.state == "stunned":
                shade.stun_left = ticks
            elif shade.state == "recoil":
                shade.recoil_left = ticks
            self.shades.append(shade)

    def _load_drifters(self, specs: list[dict]) -> None:
        used: set[str] = set()
        number = 1
        for spec in specs:
            if "id" in spec:
                drifter_id = spec["id"]
            else:
                while f"D{number}" in used:
                    number += 1
                drifter_id = f"D{number}"
                number += 1
            if drifter_id in used:
                raise FormatError(f"duplicate drifter id {drifter_id}")
            used.add(drifter_id)
            state = spec.get("state", "idle")
            flee_left = T.DRIFTER_FLEE_TICKS if state == "flee" else 0
            self.drifters.append(
                Drifter(
                    drifter_id,
                    spec["pos"][0],
                    spec["pos"][2],
                    state,
                    spec.get("stolen", 0),
                    flee_left,
                    0,
                    1.0,
                    0.0,
                    spec["pos"][1],
                )
            )

    def _load_charms(self, specs: list[dict]) -> None:
        for spec in specs:
            self.charms.append(
                Charm(spec["id"], spec["pos"][0], spec["pos"][1], spec["pos"][2], spec.get("available", True), spec.get("respawn_ticks", 0))
            )


def _shade_spawn_count(night: int, sim_tick: int) -> int:
    if night == 1:
        if sim_tick < 300 or (sim_tick - 300) % 480 != 0:
            return 0
        return 2 if sim_tick == 300 else 1
    if night == 2:
        if sim_tick < 420 or sim_tick % 420 != 0:
            return 0
        return 1
    if sim_tick < 360 or sim_tick % 360 != 0:
        return 0
    return 1


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
            if not isinstance(move, (list, tuple)) or len(move) != 2 or any(not _is_number(part) for part in move):
                raise FormatError("move must be [x, z]")
            mx, mz = float(move[0]), float(move[1])
            if mx < -1 or mx > 1 or mz < -1 or mz > 1:
                raise FormatError("move components must be in [-1, 1]")
            frame["move"] = [mx, mz]
        if "cam_yaw_deg" in raw:
            if not _is_number(raw["cam_yaw_deg"]):
                raise FormatError("cam_yaw_deg must be a number")
            frame["cam_yaw_deg"] = float(raw["cam_yaw_deg"])
        for key in ("jump", "interact", "pulse", "dash", "pause"):
            if key in raw:
                if not _is_bool(raw[key]):
                    raise FormatError(f"{key} must be a boolean")
                frame[key] = raw[key]
        frames.append(frame)
    return frames


def parse_scenario(data: object, night: int = 1) -> dict:
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
    random_drifters = _flag(data, "random_drifters", night >= 2)
    wind_enabled = _flag(data, "wind_enabled", night == 3)
    if "motes" in data:
        motes = _parse_motes(data["motes"])
    elif random_motes:
        motes = list(world.mote_points(night)[:20])
    else:
        motes = []
    if "shades" in data:
        shades = _parse_shades(data["shades"])
    else:
        shades = []
    if "drifters" in data:
        drifters = _parse_drifters(data["drifters"])
    else:
        drifters = []
    if "charms" in data:
        charms = _parse_charms(data["charms"])
    else:
        charms = [
            {"id": cid, "pos": (cx, cy, cz), "available": True, "respawn_ticks": 0}
            for cid, cx, cy, cz in world.charm_specs(night)
        ]
    lanterns = _parse_lanterns(data["lanterns"], night) if "lanterns" in data else []
    if "time_left_s" in data:
        if not _is_number(data["time_left_s"]):
            raise FormatError("time_left_s must be a number")
        time_left = float(data["time_left_s"])
        if time_left < 0:
            raise FormatError("time_left_s must be >= 0")
    else:
        time_left = float(world.duration_s(night))
    return {
        "player": {
            "pos": pos,
            "carried": carried,
            "flames": flames,
            "invuln_ticks": _as_int(player_raw["invuln_ticks"], "invuln_ticks") if "invuln_ticks" in player_raw else 0,
            "dash_cd_ticks": _as_int(player_raw["dash_cd_ticks"], "dash_cd_ticks") if "dash_cd_ticks" in player_raw else 0,
            "pulse_cd_ticks": _as_int(player_raw["pulse_cd_ticks"], "pulse_cd_ticks") if "pulse_cd_ticks" in player_raw else 0,
            "charm_ticks": _as_int(player_raw["charm_ticks"], "charm_ticks") if "charm_ticks" in player_raw else 0,
            "successful_lights": _as_int(player_raw["successful_lights"], "successful_lights") if "successful_lights" in player_raw else 0,
        },
        "motes": motes,
        "shades": shades,
        "drifters": drifters,
        "charms": charms,
        "lanterns": lanterns,
        "spawn_motes": random_motes,
        "spawn_shades": random_shades,
        "spawn_drifters": random_drifters,
        "wind_enabled": wind_enabled,
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
        if "state" in item:
            if item["state"] not in SHADE_STATES:
                raise FormatError("shade state is not a v1.2 state")
            shade["state"] = item["state"]
        if "target_lantern_id" in item:
            if not isinstance(item["target_lantern_id"], str) or not item["target_lantern_id"]:
                raise FormatError("target_lantern_id must be a non-empty string")
            shade["target_lantern_id"] = item["target_lantern_id"]
        if "state_ticks_left" in item:
            shade["state_ticks_left"] = _as_int(item["state_ticks_left"], "state_ticks_left")
        shades.append(shade)
    return shades


def _parse_drifters(value: object) -> list[dict]:
    if not isinstance(value, list):
        raise FormatError("drifters must be an array")
    drifters = []
    for item in value:
        if not isinstance(item, dict) or "pos" not in item:
            raise FormatError("drifter must be an object with pos")
        drifter = {"pos": _as_vec3(item["pos"], "drifter.pos")}
        if "id" in item:
            if not isinstance(item["id"], str) or not item["id"]:
                raise FormatError("drifter id must be a non-empty string")
            drifter["id"] = item["id"]
        if "state" in item:
            if item["state"] not in DRIFTER_STATES:
                raise FormatError("drifter state is invalid")
            drifter["state"] = item["state"]
        if "stolen" in item:
            drifter["stolen"] = _as_int(item["stolen"], "stolen")
        drifters.append(drifter)
    return drifters


def _parse_charms(value: object) -> list[dict]:
    if not isinstance(value, list):
        raise FormatError("charms must be an array")
    charms = []
    for item in value:
        if not isinstance(item, dict) or "id" not in item or "pos" not in item:
            raise FormatError("charm must have id and pos")
        charm = {"id": item["id"], "pos": _as_vec3(item["pos"], "charm.pos")}
        if "available" in item:
            if not _is_bool(item["available"]):
                raise FormatError("charm.available must be a boolean")
            charm["available"] = item["available"]
        charms.append(charm)
    return charms


def _parse_lanterns(value: object, night: int) -> list[dict]:
    if not isinstance(value, list):
        raise FormatError("lanterns must be an array")
    known = {lantern_id for lantern_id, *_rest in world.lantern_specs(night)}
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
        if "fuel" in item:
            if not _is_number(item["fuel"]) or float(item["fuel"]) < 0:
                raise FormatError("lantern.fuel must be a number >= 0")
            spec["fuel"] = float(item["fuel"])
        if "ever_lit" in item:
            if not _is_bool(item["ever_lit"]):
                raise FormatError("lantern.ever_lit must be a boolean")
            spec["ever_lit"] = item["ever_lit"]
        lanterns.append(spec)
    return lanterns


def run_simulation(
    seed: int,
    scenario: dict | None,
    frames: list[dict],
    n_ticks: int,
    snapshot_every: int,
    night: int = 1,
) -> list[dict]:
    sim = Sim.create(seed, scenario, night)
    lines = [sim.snapshot()]
    if sim.state != "playing":
        lines.append(sim.end_record())
        return lines
    held_move = [0.0, 0.0]
    held_yaw = 0.0
    held = {"jump": False, "interact": False, "pulse": False, "dash": False, "pause": False}
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
        if snapshot_every > 0 and sim.tick % snapshot_every == 0:
            lines.append(sim.snapshot())
        if sim.state in ("won", "lost"):
            break
    lines.append(sim.end_record())
    return lines
