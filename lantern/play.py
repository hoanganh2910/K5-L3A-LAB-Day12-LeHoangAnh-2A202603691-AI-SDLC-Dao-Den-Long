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
    window.color = color.rgb32(10, 8, 28)
    window.fps_counter.enabled = False
    mouse.locked = True
    camera.fov = 68
    scene.fog_color = color.rgb32(18, 10, 36)
    scene.fog_density = (36, 120)
    sun = DirectionalLight(shadows=False, rotation=(48, -40, 0))
    sun.color = color.rgb32(255, 214, 170)
    ambient = AmbientLight()
    ambient.color = color.rgb32(78, 70, 110)

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
        self.lit_shader = _lit_shader()
        self.ground_texture = _island_texture()
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
        self.Entity(
            model="quad",
            rotation_x=90,
            scale=(420, 420),
            y=-0.2,
            color=self.color.rgb32(12, 28, 58),
            double_sided=True,
        )
        self.Entity(
            model="quad",
            rotation_x=90,
            scale=(82, 82),
            y=0.02,
            texture=self.ground_texture,
            color=self.color.rgb32(210, 196, 170),
            double_sided=True,
        )
        for x, z, height in ((6, 8, 0.35), (-9, 5, 0.5), (4, -7, 0.28), (-5, -6, 0.42)):
            self.Entity(
                model="sphere",
                position=(x, height * 0.35, z),
                scale=(0.7, height, 0.55),
                color=self.color.rgb32(88, 78, 70),
                shader=self.lit_shader,
            )

    def _build_player(self):
        from ursina import Cone

        cloth = self.color.rgb32(46, 58, 96)
        skin = self.color.rgb32(236, 206, 176)
        hat = self.color.rgb32(196, 132, 48)
        shader = self.lit_shader
        self.player = self.Entity()
        self.Entity(parent=self.player, model="cube", scale=(0.22, 0.45, 0.22), position=(-0.12, 0.22, 0), color=cloth, shader=shader)
        self.Entity(parent=self.player, model="cube", scale=(0.22, 0.45, 0.22), position=(0.12, 0.22, 0), color=cloth, shader=shader)
        self.Entity(parent=self.player, model="cube", scale=(0.52, 0.72, 0.36), y=0.72, color=cloth, shader=shader)
        self.Entity(parent=self.player, model="sphere", scale=0.34, y=1.2, color=skin, shader=shader)
        self.Entity(parent=self.player, model="cube", scale=(1.2, 0.05, 1.2), y=1.32, color=hat, shader=shader)
        self.Entity(parent=self.player, model=Cone(resolution=24), scale=(1.15, 0.36, 1.15), y=1.5, color=hat, shader=shader)
        self.Entity(parent=self.player, model="sphere", scale=0.16, y=0.9, z=0.38, color=self.color.rgb32(255, 196, 90))
        self.Entity(
            parent=self.player,
            model="sphere",
            scale=0.46,
            y=0.9,
            z=0.38,
            color=self.color.rgba32(255, 170, 60, 70),
        )

    def _build_lanterns(self):
        for lantern in self.sim.lanterns:
            wood = self.color.rgb32(112, 72, 44)
            pole = self.Entity(
                model="cube",
                position=(lantern.x, 1.15, lantern.z),
                scale=(0.18, 2.3, 0.18),
                color=wood,
                shader=self.lit_shader,
            )
            self.Entity(
                model="cube",
                position=(lantern.x, 2.35, lantern.z),
                scale=(0.55, 0.08, 0.55),
                color=wood,
                shader=self.lit_shader,
            )
            glow = self.Entity(
                model="sphere",
                position=(lantern.x, 2.15, lantern.z),
                scale=0.38,
                color=self.color.rgb32(120, 90, 60),
                shader=self.lit_shader,
            )
            halo = self.Entity(
                model="sphere",
                position=(lantern.x, 2.15, lantern.z),
                scale=1.1,
                color=self.color.rgba32(255, 160, 50, 0),
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
            self.lantern_ents[lantern.id] = {"pole": pole, "glow": glow, "halo": halo, "pool": pool}

    def _build_actors(self):
        for index, mote in enumerate(self.sim.motes):
            self.mote_ents[mote.id] = self._make_mote(index)
        for shade in self.sim.shades:
            self.shade_ents[shade.id] = self._make_shade()

    def _make_mote(self, index: int):
        tint = self.color.rgb32(255, 196, 90) if index % 2 == 0 else self.color.rgb32(190, 255, 170)
        glow = self.color.rgba32(255, 210, 90, 80) if index % 2 == 0 else self.color.rgba32(180, 255, 170, 70)
        root = self.Entity()
        self.Entity(parent=root, model="sphere", scale=0.22, color=tint, shader=self.lit_shader)
        self.Entity(parent=root, model="sphere", scale=0.62, color=glow)
        return root

    def _make_shade(self):
        root = self.Entity()
        body = self.Entity(
            parent=root,
            model="sphere",
            scale=(1.45, 1.15, 1.45),
            color=self.color.rgb32(36, 10, 58),
            shader=self.lit_shader,
        )
        self.Entity(parent=root, model="sphere", scale=0.28, y=0.15, z=0.55, color=self.color.rgb32(20, 4, 28), shader=self.lit_shader)
        root.body = body
        return root

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
                ent = self._make_shade()
                self.shade_ents[shade.id] = ent
            ent.position = (shade.x, T.SHADE_CENTER_Y, shade.z)
            if shade.state == "stunned":
                ent.body.color = self.color.rgb32(150, 168, 186)
            else:
                ent.body.color = self.color.rgb32(36, 10, 58)
        lit = 0
        for lantern in sim.lanterns:
            parts = self.lantern_ents[lantern.id]
            if lantern.lit:
                lit += 1
                parts["glow"].color = self.color.rgb32(255, 186, 70)
                parts["glow"].scale = 0.55
                parts["halo"].color = self.color.rgba32(255, 160, 50, 90)
                parts["halo"].scale = 2.4
                parts["pool"].enabled = True
            else:
                parts["glow"].color = self.color.rgb32(70, 58, 48)
                parts["glow"].scale = 0.32
                parts["halo"].color = self.color.rgba32(255, 160, 50, 0)
                parts["pool"].enabled = False
        self.scene.fog_density = (36, 110 + lit * 18)
        radians = math.radians(self.yaw)
        forward_x = math.sin(radians)
        forward_z = math.cos(radians)
        self.camera.position = (
            sim.x - forward_x * 9,
            sim.y + 4.6,
            sim.z - forward_z * 9,
        )
        self.camera.look_at(Vec3_safe(sim.x, sim.y + 1.15, sim.z))
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


def _lit_shader():
    from ursina.shaders import lit_with_shadows_shader

    return lit_with_shadows_shader


def _island_texture():
    import random

    from PIL import Image
    from ursina import Texture

    rng = random.Random(1)
    size = 256
    image = Image.new("RGBA", (size, size))
    pixels = image.load()
    center = (size - 1) / 2
    radius = size * 0.47
    for y in range(size):
        for x in range(size):
            distance = math.hypot(x - center, y - center)
            if distance > radius:
                pixels[x, y] = (0, 0, 0, 0)
                continue
            edge = distance / radius
            grain = rng.randrange(-14, 15)
            grass = rng.random() < 0.07
            red = 148 + grain - int(edge * 40) - (24 if grass else 0)
            green = 132 + grain - int(edge * 24) + (22 if grass else 0)
            blue = 104 + grain - int(edge * 16)
            pixels[x, y] = tuple(max(0, min(255, channel)) for channel in (red, green, blue)) + (255,)
    return Texture(image)


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
