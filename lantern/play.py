"""Third-person window for Night 1. The view never decides the rules."""

from __future__ import annotations

import math
import sys

from lantern.sim import Sim
from lantern import tuning as T

DT = 1.0 / 60.0


def main(argv: list[str] | None = None) -> int:
    del argv
    try:
        from ursina import (
            AmbientLight,
            DirectionalLight,
            Entity,
            Text,
            Ursina,
            Vec3,
            camera,
            color,
            destroy,
            held_keys,
            mouse,
            scene,
            time,
            window,
        )
    except ImportError:
        print(
            "Ursina is required to play. Run: python3 -m pip install -r requirements.txt",
            file=sys.stderr,
        )
        return 1

    app = Ursina(
        title="Dao Den Long",
        borderless=False,
        fullscreen=False,
        size=(1280, 720),
        development_mode=False,
        show_ursina_splash=False,
    )
    window.color = color.rgb32(12, 6, 22)
    window.fps_counter.enabled = False
    mouse.locked = True
    scene.fog_color = color.rgb32(28, 14, 48)
    scene.fog_density = (30, 110)
    try:
        AmbientLight(color=color.rgba(0.35, 0.28, 0.48, 1), shadows=False)
        DirectionalLight(
            y=30,
            rotation=(50, -35, 0),
            shadows=False,
            color=color.rgb32(255, 206, 160),
        )
    except Exception:
        pass

    View(color_module=color, entity_cls=Entity, text_cls=Text, destroy=destroy, camera=camera, scene=scene)
    app.run()
    return 0


class View:
    def __init__(self, color_module, entity_cls, text_cls, destroy, camera, scene):
        self.color = color_module
        self.Entity = entity_cls
        self.destroy = destroy
        self.camera = camera
        self.scene = scene
        self.Text = text_cls
        self.yaw = 0.0
        self.acc = 0.0
        self.sim = Sim.create(T.PLAY_SEED, None)
        self.mote_ents = {}
        self.shade_ents = {}
        self.lantern_ents = {}
        self._build_island()
        self._build_player()
        self._build_lanterns()
        self._build_actors()
        ink = self.color.rgb32(255, 228, 196)
        self.hud = self.Text(text="", position=(-0.86, 0.45), origin=(-0.5, 0.5), scale=1.1, color=ink)
        self.help_text = self.Text(
            text="WASD di chuyen   Space nhay   E nap den   F toa sang   Esc chuot",
            position=(-0.86, -0.46),
            origin=(-0.5, -0.5),
            scale=0.8,
            color=ink,
        )
        self.banner = self.Text(text="", origin=(0, 0), y=0.08, scale=2, color=self.color.rgb32(255, 214, 140))
        self._root = self.Entity()
        self._root.update = self._update
        self._root.input = self._input

    def _build_island(self):
        water = self.color.rgb32(14, 22, 48)
        sand = self.color.rgb32(138, 126, 108)
        self.Entity(model="quad", rotation_x=90, scale=(220, 220), y=-0.08, color=water, double_sided=True)
        self.Entity(model="quad", rotation_x=90, scale=(80, 80), y=0, color=sand, double_sided=True)

    def _build_player(self):
        from ursina import Cone

        skin = self.color.rgb32(236, 214, 186)
        hat = self.color.rgb32(214, 164, 64)
        lamp = self.color.rgb32(255, 186, 70)
        self.player = self.Entity()
        self.Entity(parent=self.player, model="cube", scale=(0.55, 1.0, 0.38), y=0.5, color=skin)
        self.Entity(parent=self.player, model=Cone(resolution=16), scale=(1.15, 0.42, 1.15), y=1.22, color=hat)
        self.Entity(parent=self.player, model="sphere", scale=0.16, y=0.82, z=0.32, color=lamp)

    def _build_lanterns(self):
        for lantern in self.sim.lanterns:
            pole = self.Entity(
                model="cube",
                position=(lantern.x, 1.1, lantern.z),
                scale=(0.22, 2.2, 0.22),
                color=self.color.rgb32(120, 82, 52),
            )
            glow = self.Entity(
                model="sphere",
                position=(lantern.x, 2.3, lantern.z),
                scale=0.45,
                color=self.color.rgb32(90, 74, 58),
            )
            pool = self.Entity(
                model="quad",
                rotation_x=90,
                position=(lantern.x, 0.04, lantern.z),
                scale=(7, 7),
                color=self.color.rgba32(255, 170, 70, 110),
                double_sided=True,
                enabled=False,
            )
            self.lantern_ents[lantern.id] = {"pole": pole, "glow": glow, "pool": pool}

    def _build_actors(self):
        for index, mote in enumerate(self.sim.motes):
            tint = self.color.rgb32(255, 196, 90) if index % 2 == 0 else self.color.rgb32(210, 255, 170)
            self.mote_ents[mote.id] = self.Entity(model="sphere", scale=0.28, color=tint)
        for shade in self.sim.shades:
            self.shade_ents[shade.id] = self.Entity(
                model="sphere",
                scale=1.15,
                color=self.color.rgb32(46, 16, 72),
            )

    def _input(self, key):
        from ursina import mouse

        if key == "escape":
            mouse.locked = not mouse.locked
        if key == "r" and self.sim.state != "playing":
            self._restart()

    def _restart(self):
        for ent in list(self.mote_ents.values()) + list(self.shade_ents.values()):
            self.destroy(ent)
        self.mote_ents.clear()
        self.shade_ents.clear()
        self.sim = Sim.create(T.PLAY_SEED, None)
        self.yaw = 0.0
        self.acc = 0.0
        self._build_actors()

    def _update(self):
        from ursina import mouse, time

        if mouse.locked:
            self.yaw += mouse.velocity[0] * 90
        self.acc = min(0.25, self.acc + time.dt)
        if self.sim.state == "playing":
            while self.acc >= DT:
                self._step_live()
                self.acc -= DT
        self._sync(time.time())

    def _step_live(self):
        from ursina import held_keys

        move_x = _axis("d", "right arrow") - _axis("a", "left arrow")
        move_z = _axis("w", "up arrow") - _axis("s", "down arrow")
        self.sim.set_input(
            [move_x, move_z],
            self.yaw,
            {
                "jump": bool(held_keys["space"]),
                "interact": bool(held_keys["e"]),
                "pulse": bool(held_keys["f"]),
            },
        )
        self.sim.step()

    def _sync(self, now: float):
        sim = self.sim
        self.player.position = (sim.x, sim.y, sim.z)
        self.player.rotation_y = self.yaw
        alive = {mote.id: mote for mote in sim.motes}
        for mote_id, ent in list(self.mote_ents.items()):
            mote = alive.get(mote_id)
            if mote is None:
                self.destroy(ent)
                del self.mote_ents[mote_id]
                continue
            bob = 0.55 + math.sin(now * 3 + (id_number(mote_id) * 0.7)) * 0.14
            ent.position = (mote.x, bob, mote.z)
        for shade in sim.shades:
            ent = self.shade_ents.get(shade.id)
            if ent is None:
                ent = self.Entity(model="sphere", scale=1.15, color=self.color.rgb32(46, 16, 72))
                self.shade_ents[shade.id] = ent
            ent.position = (shade.x, T.SHADE_CENTER_Y, shade.z)
            if shade.state == "stunned":
                ent.color = self.color.rgb32(150, 170, 190)
            else:
                ent.color = self.color.rgb32(46, 16, 72)
        lit = 0
        for lantern in sim.lanterns:
            parts = self.lantern_ents[lantern.id]
            if lantern.lit:
                lit += 1
                parts["glow"].color = self.color.rgb32(255, 176, 64)
                parts["glow"].scale = 0.7
                parts["pool"].enabled = True
            else:
                parts["glow"].color = self.color.rgb32(90, 74, 58)
                parts["glow"].scale = 0.45
                parts["pool"].enabled = False
        self.scene.fog_density = (30, 100 + lit * 16)
        radians = math.radians(self.yaw)
        forward_x = math.sin(radians)
        forward_z = math.cos(radians)
        self.camera.position = (
            sim.x - forward_x * 8,
            sim.y + 3.4,
            sim.z - forward_z * 8,
        )
        self.camera.look_at(Vec3_safe(sim.x, sim.y + 1.0, sim.z))
        remaining = max(0.0, sim.duration_s - sim.steps / 60.0)
        self.hud.text = (
            f"Dem 1    {remaining:5.1f}s\n"
            f"Diem     {sim.score}\n"
            f"Mau      {sim.flames}\n"
            f"Dom dom  {sim.carried}/{T.CARRY_CAPACITY}\n"
            f"Den      {lit}/5"
        )
        if sim.state == "won":
            self.banner.text = "Thang\nNhan R de choi lai"
        elif sim.state == "lost":
            self.banner.text = "Thua\nNhan R de choi lai"
        else:
            self.banner.text = ""


def _axis(primary: str, secondary: str) -> float:
    from ursina import held_keys

    return 1.0 if held_keys[primary] or held_keys[secondary] else 0.0


def id_number(identifier: str) -> int:
    digits = "".join(ch for ch in identifier if ch.isdigit())
    return int(digits) if digits else 0


def Vec3_safe(x, y, z):
    from ursina import Vec3

    return Vec3(x, y, z)


if __name__ == "__main__":
    sys.exit(main())
