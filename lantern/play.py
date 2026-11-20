"""Third-person window. The view reads the sim and never decides a rule."""

from __future__ import annotations

import math
import struct
import sys
import wave
from pathlib import Path

from lantern import tuning as T
from lantern import world
from lantern.sim import Sim

DT = T.DT
UI = "#F5F1E6"
DANGER = "#FF5A5F"
GOLD = "#F2C14E"
INTROS = {
    1: ("Đêm 1 — Đảo Bến", "Ông Đăng: Năm ngọn đèn chờ con. Nhặt đom đóm, và đừng để Bóng Mực chạm khăn."),
    2: ("Đêm 2 — Đảo Cau", "Ông Đăng: Cầu tre nối hai đảo. Gió Lạc thèm ánh sáng trong túi con."),
    3: ("Đêm 3 — Đảo Chuông", "Ông Đăng: Leo tầng, nghe gió trước khi nó đẩy. Bảy đèn là bình minh."),
}


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    bench = "--bench" in args
    try:
        from ursina import AmbientLight, DirectionalLight, Text, Ursina, camera, color, mouse, scene, window
    except ImportError:
        print("Ursina is required to play. Run: python3 -m pip install -r requirements.txt", file=sys.stderr)
        return 1
    app = Ursina(
        title="Dao Den Long",
        borderless=False,
        fullscreen=False,
        size=(1280, 720),
        window_type="offscreen" if bench else "onscreen",
        development_mode=False,
        show_ursina_splash=False,
    )
    window.color = _hex(color, "#0E1430")
    window.fps_counter.enabled = False
    window.exit_button.enabled = False
    if not bench:
        mouse.locked = False
    camera.fov = 68
    scene.fog_color = _hex(color, "#1B2350")
    scene.fog_density = (40, 130)
    sun = DirectionalLight(shadows=False, rotation=(50, -35, 0))
    sun.color = _hex(color, "#FFE9B0")
    ambient = AmbientLight()
    ambient.color = _hex(color, "#0E1430")
    Game(color, Text, camera, scene, ambient, bench)
    app.run()
    return 0


class Game:
    def __init__(self, color_module, text_cls, camera, scene, ambient, bench: bool):
        from ursina import Entity

        self.color = color_module
        self.Text = text_cls
        self.Entity = Entity
        self.camera = camera
        self.scene = scene
        self.ambient = ambient
        self.bench = bench
        self.shader = _shader()
        self.sounds = _sounds()
        self.settings = _load_settings()
        self.mode = "menu"
        self.night = 1
        self.scores: list[int] = []
        self.yaw = 0.0
        self.acc = 0.0
        self.sim: Sim | None = None
        self.was_grounded = True
        self.last_second = None
        self.frames = 0
        self.bench_started = None
        self.world_ents = []
        self.mote_ents = {}
        self.shade_ents = {}
        self.drifter_ents = {}
        self.charm_ents = {}
        self.lantern_ents = {}
        self.player = None
        ink = _hex(color_module, UI)
        self.flames = text_cls(text="", position=(-0.86, 0.46), origin=(-0.5, 0.5), scale=1.15, color=_hex(color_module, DANGER))
        self.clock = text_cls(text="", position=(0, 0.46), origin=(0, 0.5), scale=1.4, color=ink)
        self.stats = text_cls(text="", position=(0.86, 0.46), origin=(0.5, 0.5), scale=1.05, color=_hex(color_module, GOLD))
        self.pips = text_cls(text="", position=(0, -0.42), origin=(0, 0), scale=1.3, color=_hex(color_module, "#FFF6C2"))
        self.cooldowns = text_cls(text="", position=(0.86, -0.42), origin=(0.5, 0), scale=0.9, color=ink)
        self.prompt = text_cls(text="", position=(0, -0.28), origin=(0, 0), scale=1.0, color=ink)
        self.arrow = text_cls(text="", position=(0, 0), origin=(0, 0), scale=1.4, color=_hex(color_module, GOLD))
        self.banner = text_cls(text="", origin=(0, 0), scale=1.6, color=ink)
        self.help_text = text_cls(text="", position=(0, -0.48), origin=(0, 0), scale=0.7, color=ink)
        self._root = Entity()
        self._root.update = self._update
        self._root.input = self._input
        self._show_menu()
        if bench:
            self._begin_night()

    def _hx(self, value: str, alpha: int = 255):
        return _hex(self.color, value, alpha)

    def _show_menu(self) -> None:
        self.mode = "menu"
        self._hide_hud()
        self.banner.text = "Đảo Đèn Lồng\n\nEnter — Bắt đầu"
        self.help_text.text = "Ba đêm. Thắp hết đèn trước bình minh."
        self._music(False)

    def _show_intro(self) -> None:
        self.mode = "intro"
        title, line = INTROS[self.night]
        self.banner.text = f"{title}\n\n{line}\n\nEnter — Đi"
        self.help_text.text = ""

    def _begin_night(self) -> None:
        self._clear_world()
        self.sim = Sim.create(T.PLAY_SEED + self.night, None, self.night)
        self.yaw = 0.0
        self.acc = 0.0
        self.was_grounded = True
        self.last_second = None
        self._build_world()
        self._build_player()
        self.mode = "play"
        self.banner.text = ""
        self._show_hud()
        from ursina import mouse

        if not self.bench:
            mouse.locked = True
        self._music(True)

    def _finish_night(self) -> None:
        sim = self.sim
        self._music(False)
        if sim.state == "won":
            self._play("win")
            self.scores.append(sim.score)
            if self.night == 3:
                self.mode = "dawn"
                total = sum(self.scores)
                self.banner.text = f"Bình Minh\n\nTổng điểm {total}\n\nEnter — Về menu"
                self._hide_hud()
                return
            self.mode = "result"
            self.banner.text = f"Đêm {self.night} sáng\nĐiểm {sim.score}\n\nEnter — Đêm sau"
        else:
            self._play("lose")
            self.mode = "result"
            self.banner.text = f"Đêm {self.night} tắt\n\nEnter — Chơi lại đêm này"
        self._hide_hud()

    def _input(self, key: str) -> None:
        if key in ("escape", "p") and self.mode == "play":
            self.mode = "pause"
            self.banner.text = "Tạm dừng\n\n1 Tiếp tục\n2 Chơi lại Đêm\n3 Cài đặt\n4 Về menu"
            self._music(False)
            from ursina import mouse

            mouse.locked = False
            return
        if self.mode == "pause":
            if key == "1":
                self.mode = "play"
                self.banner.text = ""
                self._music(True)
                from ursina import mouse

                mouse.locked = True
            elif key == "2":
                self._begin_night()
            elif key == "3":
                self.mode = "settings"
                self._settings_text()
            elif key == "4":
                self.scores.clear()
                self.night = 1
                self._clear_world()
                self.sim = None
                self._show_menu()
            return
        if self.mode == "settings":
            if key == "left arrow":
                self.settings["volume"] = max(0.0, round(self.settings["volume"] - 0.1, 2))
            elif key == "right arrow":
                self.settings["volume"] = min(1.0, round(self.settings["volume"] + 0.1, 2))
            elif key == "down arrow":
                self.settings["sensitivity"] = max(0.2, round(self.settings["sensitivity"] - 0.1, 2))
            elif key == "up arrow":
                self.settings["sensitivity"] = min(3.0, round(self.settings["sensitivity"] + 0.1, 2))
            elif key == "enter":
                _save_settings(self.settings)
                self.mode = "pause"
                self.banner.text = "Tạm dừng\n\n1 Tiếp tục\n2 Chơi lại Đêm\n3 Cài đặt\n4 Về menu"
                return
            _save_settings(self.settings)
            self._settings_text()
            return
        if key == "enter":
            if self.mode == "menu":
                self.night = 1
                self.scores = []
                self._show_intro()
            elif self.mode == "intro":
                self._begin_night()
            elif self.mode == "result":
                if self.sim and self.sim.state == "won":
                    self.night += 1
                    self._show_intro()
                else:
                    self._begin_night()
            elif self.mode == "dawn":
                self.night = 1
                self.scores = []
                self._clear_world()
                self.sim = None
                self._show_menu()

    def _settings_text(self) -> None:
        self.banner.text = (
            f"Cài đặt\n\nÂm lượng {self.settings['volume']:.1f}   ← →\n"
            f"Độ nhạy chuột {self.settings['sensitivity']:.1f}   ↑ ↓\n\nEnter — Quay lại"
        )

    def _update(self) -> None:
        from ursina import time

        if self.bench:
            self._bench_frame()
        if self.mode != "play" or self.sim is None:
            return
        from ursina import mouse

        if mouse.locked:
            self.yaw += mouse.velocity[0] * 70 * self.settings["sensitivity"]
        self.acc = min(0.25, self.acc + time.dt)
        while self.acc >= DT:
            self._step_live()
            self.acc -= DT
            if self.sim.state != "playing":
                self._finish_night()
                return
        self._sync(time.time())

    def _bench_frame(self) -> None:
        import time as clock

        from ursina import application

        if self.bench_started is None:
            self.bench_started = clock.perf_counter()
        self.frames += 1
        if self.frames >= 180:
            elapsed = clock.perf_counter() - self.bench_started
            print(f"fps {180 / elapsed:.1f}")
            application.quit()

    def _step_live(self) -> None:
        from ursina import held_keys

        sim = self.sim
        grounded = sim.grounded
        move_x = _axis("d", "right arrow") - _axis("a", "left arrow")
        move_z = _axis("w", "up arrow") - _axis("s", "down arrow")
        jump = bool(held_keys["space"])
        sim.set_input(
            [move_x, move_z],
            self.yaw,
            {
                "jump": jump,
                "interact": bool(held_keys["e"]),
                "pulse": bool(held_keys["f"]),
                "dash": bool(held_keys["left shift"]),
                "pause": False,
            },
        )
        happened = sim.step()
        if jump and grounded and not sim.grounded:
            self._play("jump")
        for event in happened:
            name = event["name"]
            if name == "mote_picked":
                self._play("pick")
            elif name == "lantern_lit":
                self._play("lit")
            elif name == "pulse":
                self._play("pulse")
            elif name == "player_hit":
                self._play("hit")
            elif name == "dash":
                self._play("dash")
            elif name == "shade_spawned":
                self._play("spawn")
        left = max(0.0, sim.duration_s - sim.sim_tick / 60.0)
        second = math.ceil(left) if left > 0 else 0
        if second != self.last_second and 1 <= second <= 10:
            self._play("tick")
        self.last_second = second

    def _sync(self, now: float) -> None:
        sim = self.sim
        self.player.position = (sim.x, sim.y, sim.z)
        if math.hypot(sim.vx, sim.vz) > 0.2:
            self.player.rotation_y = math.degrees(math.atan2(sim.vx, sim.vz))
        self._sync_motes(now)
        self._sync_shades()
        self._sync_drifters(now)
        self._sync_charms()
        lit = 0
        for lantern in sim.lanterns:
            parts = self.lantern_ents[lantern.id]
            if lantern.lit:
                lit += 1
                parts["glow"].color = self._hx("#FFB347")
                parts["core"].color = self._hx("#FFE9B0")
                parts["pool"].enabled = True
            else:
                parts["glow"].color = self._hx("#5B5F6E")
                parts["core"].color = self._hx("#5B5F6E")
                parts["pool"].enabled = False
        total = max(1, len(sim.lanterns))
        level = 0.15 + 0.55 * (lit / total)
        self.ambient.color = self.color.rgb32(int(255 * level), int(250 * level), int(255 * level))
        self._camera()
        self._hud(lit, now)

    def _hud(self, lit: int, now: float) -> None:
        sim = self.sim
        left = max(0.0, sim.duration_s - sim.sim_tick / 60.0)
        self.flames.text = "Ngon Lua  " + "*" * sim.flames + "." * (T.FLAMES - sim.flames)
        self.clock.text = f"{int(left) // 60:02d}:{int(left) % 60:02d}"
        if left <= 30:
            self.clock.color = self._hx(DANGER if int(now * 2) % 2 == 0 else "#3A1214")
        else:
            self.clock.color = self._hx(UI)
        self.stats.text = f"Den {lit}/{len(sim.lanterns)}\nDiem {sim.score}"
        self.pips.text = "#" * sim.carried + "-" * (T.CARRY_CAPACITY - sim.carried)
        dash = "Lướt sẵn" if sim.dash_cd == 0 or sim.charm_left > 0 else f"Lướt {sim.dash_cd / 60:.1f}"
        pulse = "Sáng sẵn" if sim.pulse_cd == 0 else f"Sáng {sim.pulse_cd / 60:.1f}"
        self.cooldowns.text = f"{dash}\n{pulse}"
        self.prompt.text = ""
        self.arrow.text = ""
        nearest = None
        for lantern in sim.lanterns:
            if lantern.lit:
                continue
            dist = math.hypot(lantern.x - sim.x, lantern.z - sim.z)
            if nearest is None or dist < nearest[0]:
                nearest = (dist, lantern)
        if nearest is None:
            return
        dist, lantern = nearest
        if dist <= T.INTERACT_RADIUS:
            self.prompt.text = f"E - Nap anh sang ({lantern.deposited}/{T.LANTERN_COST})"
            return
        dx = lantern.x - sim.x
        dz = lantern.z - sim.z
        angle = math.atan2(dx, dz) - math.radians(self.yaw)
        while angle > math.pi:
            angle -= math.tau
        while angle < -math.pi:
            angle += math.tau
        if abs(angle) > math.radians(32):
            self.arrow.text = ">"
            self.arrow.position = (max(-0.78, min(0.78, math.sin(angle) * 0.9)), max(-0.3, min(0.3, math.cos(angle) * 0.35)))

    def _camera(self) -> None:
        from ursina import Vec3

        sim = self.sim
        radians = math.radians(self.yaw)
        self.camera.position = (sim.x - math.sin(radians) * 9, sim.y + 4.8, sim.z - math.cos(radians) * 9)
        self.camera.look_at(Vec3(sim.x, sim.y + 1.2, sim.z))

    def _build_world(self) -> None:
        sea = self._quad(420 if self.night == 1 else 520, self._hx("#12384A"), y=-0.35)
        if self.night == 2:
            sea.x = 35
        grass = self._hx("#2F5D50")
        sand = self._hx("#C9B48A")
        wood = self._hx("#6B4A2F")
        if self.night == 1:
            self._quad(80, grass, y=0.0)
        elif self.night == 2:
            self._quad(56, grass, y=0.0)
            other = self._quad(56, grass, y=0.0)
            other.x = 70
            bridge = self._quad(1, wood, y=0.02)
            bridge.x = 35
            bridge.scale = (18, 4)
        else:
            self._quad(90, grass, y=0.0)
            upper = self._quad(48, sand, y=3.0)
            upper.z = 12
            upper.scale = (48, 24)
            crown = self._quad(16, sand, y=6.02)
            bell = self.Entity(model="cube", position=(0, 10, 0), scale=(4, 8, 4), color=wood, shader=self.shader)
            self.world_ents.append(bell)
            for deg in (30, 150):
                rad = math.radians(deg)
                ramp = self.Entity(
                    model="cube",
                    position=(27 * math.cos(rad), 1.5, 27 * math.sin(rad)),
                    scale=(3, 0.2, 7),
                    rotation=(26, -deg, 0),
                    color=sand,
                    shader=self.shader,
                )
                self.world_ents.append(ramp)
        for pad in world.pads(self.night):
            mark = self._quad(2, self._hx(GOLD), y=pad["y"] + 0.04)
            mark.x = pad["x"]
            mark.z = pad["z"]
        for lantern in self.sim.lanterns:
            pole = self.Entity(model="cube", position=(lantern.x, lantern.y + 1.2, lantern.z), scale=(0.18, 2.4, 0.18), color=wood, shader=self.shader)
            cap = self.Entity(model="cube", position=(lantern.x, lantern.y + 2.45, lantern.z), scale=(0.55, 0.08, 0.55), color=wood, shader=self.shader)
            glow = self.Entity(model="sphere", position=(lantern.x, lantern.y + 2.15, lantern.z), scale=0.42, color=self._hx("#5B5F6E"), shader=self.shader)
            core = self.Entity(model="sphere", position=(lantern.x, lantern.y + 2.15, lantern.z), scale=0.18, color=self._hx("#5B5F6E"))
            pool = self._quad(8, self._hx("#FFB347", 90), y=lantern.y + 0.05)
            pool.x, pool.z = lantern.x, lantern.z
            pool.enabled = False
            self.world_ents.extend((pole, cap, glow, core, pool))
            self.lantern_ents[lantern.id] = {"glow": glow, "core": core, "pool": pool}

    def _build_player(self) -> None:
        from ursina import Cone

        cloth = self._hx("#E8E2D0")
        scarf = self._hx("#C8102E")
        skin = self._hx("#E6C2A6")
        wood = self._hx("#6B4A2F")
        self.player = self.Entity()
        parts = [
            self.Entity(parent=self.player, model="cube", scale=(0.28, 0.5, 0.28), position=(-0.12, 0.25, 0), color=cloth, shader=self.shader),
            self.Entity(parent=self.player, model="cube", scale=(0.28, 0.5, 0.28), position=(0.12, 0.25, 0), color=cloth, shader=self.shader),
            self.Entity(parent=self.player, model="cube", scale=(0.62, 0.75, 0.36), y=0.78, color=cloth, shader=self.shader),
            self.Entity(parent=self.player, model="cube", scale=(0.66, 0.16, 0.4), y=1.02, color=scarf, shader=self.shader),
            self.Entity(parent=self.player, model="sphere", scale=0.32, y=1.28, color=skin, shader=self.shader),
            self.Entity(parent=self.player, model="cube", scale=(0.9, 0.04, 0.9), y=1.4, color=wood, shader=self.shader),
            self.Entity(parent=self.player, model=Cone(resolution=16), scale=(0.7, 0.28, 0.7), y=1.52, color=wood, shader=self.shader),
        ]
        self.world_ents.extend(parts)
        self.world_ents.append(self.player)

    def _sync_motes(self, now: float) -> None:
        alive = {mote.id: mote for mote in self.sim.motes}
        for mote_id, ent in list(self.mote_ents.items()):
            if mote_id not in alive:
                self._drop(ent)
                del self.mote_ents[mote_id]
        for mote in self.sim.motes:
            ent = self.mote_ents.get(mote.id)
            if ent is None:
                ent = self._orb("#FFF6C2", "#FFE58A", 0.18)
                self.mote_ents[mote.id] = ent
            ent.position = (mote.x, mote.y + 0.45 + math.sin(now * 3) * 0.08, mote.z)

    def _sync_shades(self) -> None:
        alive = {shade.id: shade for shade in self.sim.shades}
        for shade_id, ent in list(self.shade_ents.items()):
            if shade_id not in alive:
                self._drop(ent)
                del self.shade_ents[shade_id]
        for shade in self.sim.shades:
            ent = self.shade_ents.get(shade.id)
            if ent is None:
                ent = self.Entity()
                body = self.Entity(parent=ent, model="sphere", scale=(1.4, 1.5, 1.4), color=self._hx("#120A1A"), shader=self.shader)
                edge = self.Entity(parent=ent, model="sphere", scale=(1.7, 1.7, 1.7), color=self._hx("#7A3CFF", 70))
                ent.body = body
                ent.edge = edge
                self.shade_ents[shade.id] = ent
            ent.position = (shade.x, shade.y, shade.z)
            if shade.state == "stunned":
                ent.body.color = self._hx("#3A3450")
                ent.edge.color = self._hx("#3A3450", 80)
            else:
                ent.body.color = self._hx("#120A1A")
                ent.edge.color = self._hx("#7A3CFF", 70)

    def _sync_drifters(self, now: float) -> None:
        alive = {item.id: item for item in self.sim.drifters}
        for item_id, ent in list(self.drifter_ents.items()):
            if item_id not in alive:
                self._drop(ent)
                del self.drifter_ents[item_id]
        for item in self.sim.drifters:
            ent = self.drifter_ents.get(item.id)
            if ent is None:
                ent = self.Entity(model="cube", scale=(0.2, 0.9, 1.6), color=self._hx("#8FA3B8"), shader=self.shader)
                self.drifter_ents[item.id] = ent
            ent.position = (item.x, 1.2 + math.sin(now * 2) * 0.1, item.z)

    def _sync_charms(self) -> None:
        for charm in self.sim.charms:
            ent = self.charm_ents.get(charm.id)
            if ent is None:
                ent = self.Entity(model="cube", scale=(0.45, 0.08, 0.7), color=self._hx("#C8102E"), shader=self.shader)
                self.Entity(parent=ent, model="cube", scale=(1.05, 0.4, 1.05), color=self._hx(GOLD))
                self.charm_ents[charm.id] = ent
            ent.position = (charm.x, charm.y + 0.3, charm.z)
            ent.enabled = charm.available

    def _quad(self, size: float, tint, y: float):
        ent = self.Entity(model="quad", rotation_x=90, scale=(size, size), y=y, color=tint, double_sided=True)
        self.world_ents.append(ent)
        return ent

    def _orb(self, core: str, halo: str, scale: float):
        ent = self.Entity()
        self.Entity(parent=ent, model="sphere", scale=scale, color=self._hx(core))
        self.Entity(parent=ent, model="sphere", scale=scale * 2.4, color=self._hx(halo, 80))
        return ent

    def _drop(self, ent) -> None:
        from ursina import destroy

        destroy(ent)

    def _clear_world(self) -> None:
        from ursina import destroy

        for ent in self.world_ents:
            destroy(ent)
        for group in (self.mote_ents, self.shade_ents, self.drifter_ents, self.charm_ents):
            for ent in group.values():
                destroy(ent)
            group.clear()
        self.lantern_ents.clear()
        self.world_ents.clear()
        self.player = None

    def _hide_hud(self) -> None:
        for item in (self.flames, self.clock, self.stats, self.pips, self.cooldowns, self.prompt, self.arrow):
            item.text = ""

    def _show_hud(self) -> None:
        self.help_text.text = "WASD đi   Space nhảy   Shift lướt   E nạp   F tỏa sáng   Esc dừng"

    def _play(self, name: str) -> None:
        sound = self.sounds.get(name)
        if sound is None:
            return
        sound.volume = self.settings["volume"]
        sound.play()

    def _music(self, playing: bool) -> None:
        music = self.sounds.get("music")
        if music is None:
            return
        music.volume = self.settings["volume"] * 0.35
        if playing and not getattr(music, "_started", False):
            music.play()
            music._started = True
        music.volume = self.settings["volume"] * (0.35 if playing else 0.0)


def _hex(color_module, value: str, alpha: int = 255):
    raw = value.lstrip("#")
    red, green, blue = int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)
    return color_module.rgba32(red, green, blue, alpha)


def _shader():
    from ursina.shaders import lit_with_shadows_shader

    return lit_with_shadows_shader


def _axis(primary: str, secondary: str) -> float:
    from ursina import held_keys

    return 1.0 if held_keys[primary] or held_keys[secondary] else 0.0


def _settings_path() -> Path:
    folder = Path.home() / ".dao-den-long"
    folder.mkdir(exist_ok=True)
    return folder / "settings.json"


def _load_settings() -> dict:
    import json

    path = _settings_path()
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return {
                "volume": float(data.get("volume", 0.7)),
                "sensitivity": float(data.get("sensitivity", 1.0)),
            }
        except (OSError, ValueError, TypeError):
            pass
    return {"volume": 0.7, "sensitivity": 1.0}


def _save_settings(settings: dict) -> None:
    import json

    _settings_path().write_text(json.dumps(settings), encoding="utf-8")


def _tone(path: Path, freqs: list[float], ms: int, volume: float = 0.35) -> None:
    rate = 22050
    count = int(rate * ms / 1000)
    with wave.open(str(path), "w") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        frames = bytearray()
        for index in range(count):
            sample = 0.0
            for freq in freqs:
                sample += math.sin(2 * math.pi * freq * index / rate)
            sample = int(volume * 32767 * sample / len(freqs))
            frames += struct.pack("<h", max(-32767, min(32767, sample)))
        handle.writeframes(frames)


def _sounds() -> dict:
    try:
        from ursina import Audio
    except ImportError:
        return {}
    folder = Path.home() / ".dao-den-long" / "tones"
    folder.mkdir(parents=True, exist_ok=True)
    notes = {
        "pick": ([880, 1320], 90),
        "lit": ([523, 659, 784], 280),
        "pulse": ([440, 880], 160),
        "hit": ([196, 140], 180),
        "jump": ([520], 70),
        "dash": ([700, 980], 90),
        "win": ([523, 659, 784, 1046], 420),
        "lose": ([311, 233, 174], 360),
        "spawn": ([180, 240], 220),
        "tick": ([988], 60),
        "music": ([196, 247, 294], 1600),
    }
    sounds = {}
    for name, (freqs, ms) in notes.items():
        path = folder / f"{name}.wav"
        if not path.exists():
            _tone(path, freqs, ms, 0.22 if name == "music" else 0.4)
        sounds[name] = Audio(path, autoplay=False, loop=name == "music")
    return sounds


if __name__ == "__main__":
    sys.exit(main())
