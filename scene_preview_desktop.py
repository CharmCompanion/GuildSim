"""Desktop preview for Pico scenes without flashing hardware.

Runs PicoGuildSim with mocked machine/LCD modules and renders frames in Tkinter.
"""

import sys
import time
import types
import tkinter as tk
import random


# ---- MicroPython time compatibility ----
if not hasattr(time, "ticks_ms"):
    _t0 = time.monotonic()

    def ticks_ms():
        return int((time.monotonic() - _t0) * 1000)

    def ticks_diff(a, b):
        return a - b

    def ticks_add(a, b):
        return a + b

    def sleep_ms(ms):
        time.sleep(ms / 1000.0)

    time.ticks_ms = ticks_ms
    time.ticks_diff = ticks_diff
    time.ticks_add = ticks_add
    time.sleep_ms = sleep_ms


# ---- Mock machine module ----
machine = types.ModuleType("machine")


class Pin:
    IN = 0
    OUT = 1
    PULL_UP = 2

    def __init__(self, pin, mode=None, pull=None, value=1):
        self.pin = pin
        self.mode = mode
        self.pull = pull
        self._value = value

    def value(self, v=None):
        if v is None:
            return self._value
        self._value = v

    def __call__(self, v=None):
        if v is None:
            return self._value
        self._value = v


class PWM:
    def __init__(self, pin):
        self.pin = pin
        self._freq = 1000
        self._duty = 0

    def freq(self, f=None):
        if f is None:
            return self._freq
        self._freq = f

    def duty_u16(self, d):
        self._duty = d


class I2C:
    def __init__(self, i2c_id, sda=None, scl=None):
        self.i2c_id = i2c_id
        self.sda = sda
        self.scl = scl

    def writeto(self, addr, data):
        _ = (addr, data)

    def readfrom(self, addr, n):
        _ = addr
        # Return centered joystick-ish values.
        if n <= 0:
            return bytes()
        return bytes([128] * n)


machine.Pin = Pin
machine.PWM = PWM
machine.I2C = I2C
sys.modules["machine"] = machine


# ---- Mock LCD module ----
lcd = types.ModuleType("lcd")


def _rgb565_to_hex(c):
    r = (c >> 11) & 0x1F
    g = (c >> 5) & 0x3F
    b = c & 0x1F
    r8 = (r * 255) // 31
    g8 = (g * 255) // 63
    b8 = (b * 255) // 31
    return "#%02x%02x%02x" % (r8, g8, b8)


class LCD_1inch8:
    WIDTH = 128
    HEIGHT = 160

    def __init__(self):
        self.width = self.WIDTH
        self.height = self.HEIGHT
        self.ops = []

    def fill(self, color):
        self.ops = [("fill", color)]

    def fill_rect(self, x, y, w, h, color):
        self.ops.append(("fill_rect", x, y, w, h, color))

    def rect(self, x, y, w, h, color):
        self.ops.append(("rect", x, y, w, h, color))

    def pixel(self, x, y, color):
        self.ops.append(("pixel", x, y, color))

    def text(self, txt, x, y, color):
        self.ops.append(("text", txt, x, y, color))

    def show(self):
        pass


lcd.LCD_1inch8 = LCD_1inch8
sys.modules["lcd"] = lcd


# Import after mocks are installed.
from models import default_guild, generate_recruit, seed_recruit_pool, get_available_missions
from pico_app import PicoGuildSim


class ScenePreview:
    SCALE = 4

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("GuildSim Pico Scene Preview")
        self.canvas = tk.Canvas(self.root, width=128 * self.SCALE, height=160 * self.SCALE, bg="#000")
        self.canvas.pack()

        self.info = tk.Label(
            self.root,
            text="1..9 scenes | arrows move | Z=A | X=B | C=stick mode toggle | A/D tab left/right",
            anchor="w",
            justify="left",
        )
        self.info.pack(fill="x")

        self.sim = PicoGuildSim()
        self._load_demo_state()

        self.bind_keys()
        self.redraw()

    def _load_demo_state(self):
        random.seed(1337)
        slot = "slot_preview"
        guild = default_guild("Preview Guild", "Commander")
        guild["rank"] = 3
        guild["gold"] = 850
        guild["soul_gems"] = 4
        guild["total_missions"] = 18
        guild["successful_missions"] = 11
        guild["unlocked_categories"] = ["melee", "magic", "range", "passive"]
        guild["mission_log"] = [
            "=== Mission: Wyvern Hunt ===",
            "Party Power: 186 vs Difficulty: 90",
            "Success Chance: 95% | Roll: 54",
            "SUCCESS! Earned 214g",
            "  Knox: +88 XP [LEVEL UP!]",
            "  Luna: +83 XP",
            "=== Mission: Bandit Ambush ===",
            "FAILED!",
            "  Reed was injured! (-11 HP, recovering...)",
        ]

        roster = [generate_recruit(guild["rank"]) for _ in range(9)]
        for idx, r in enumerate(roster):
            r["level"] = 1 + (idx % 4)
            r["xp"] = 20 + idx * 11
            r["is_active"] = idx < 4
            if idx == 2:
                r["injury_timer"] = 28
                r["current_hp"] = max(1, r["stats"]["HP"] - 9)
            if idx == 4:
                r["fatigue"] = 72
            r["training_xp"]["melee"] = 12 + idx * 6
            r["training_xp"]["magic"] = 7 + idx * 4
            r["training_xp"]["range"] = 5 + idx * 3
            r["training_xp"]["passive"] = 3 + idx * 2

        self.sim.slot = slot
        self.sim.guild = guild
        self.sim.roster = roster
        self.sim.scene = "dashboard"
        self.sim.cursor = 0

        self.sim.recruit_pools[slot] = seed_recruit_pool(guild["rank"], 6)
        self.sim.available_missions[slot] = get_available_missions(guild["rank"])
        if roster:
            self.sim.selected_recruit_id = roster[0]["id"]

    def bind_keys(self):
        self.root.bind("<KeyPress-1>", lambda e: self.set_scene("save_slots"))
        self.root.bind("<KeyPress-2>", lambda e: self.set_scene("dashboard"))
        self.root.bind("<KeyPress-3>", lambda e: self.set_scene("roster"))
        self.root.bind("<KeyPress-4>", lambda e: self.set_scene("tavern"))
        self.root.bind("<KeyPress-5>", lambda e: self.set_scene("recruit"))
        self.root.bind("<KeyPress-6>", lambda e: self.set_scene("missions"))
        self.root.bind("<KeyPress-7>", lambda e: self.set_scene("training"))
        self.root.bind("<KeyPress-8>", lambda e: self.set_scene("settings"))
        self.root.bind("<KeyPress-9>", lambda e: self.set_scene("log"))

        self.root.bind("<Up>", lambda e: self.send_move("up"))
        self.root.bind("<Down>", lambda e: self.send_move("down"))
        self.root.bind("<Left>", lambda e: self.send_move("left"))
        self.root.bind("<Right>", lambda e: self.send_move("right"))
        self.root.bind("<KeyPress-z>", lambda e: self.send_buttons(a=True))
        self.root.bind("<KeyPress-x>", lambda e: self.send_buttons(b=True))
        self.root.bind("<KeyPress-c>", lambda e: self.send_buttons(stick=True))

        # Convenience: direct tab stepping in recruit scene.
        self.root.bind("<KeyPress-a>", lambda e: self.send_move("left"))
        self.root.bind("<KeyPress-d>", lambda e: self.send_move("right"))

    def default_events(self):
        return {
            "move": None,
            "a_pressed": False,
            "b_pressed": False,
            "stick_pressed": False,
            "raw_x": 128,
            "raw_y": 128,
        }

    def send_move(self, direction):
        ev = self.default_events()
        ev["move"] = direction
        self.sim.handle_input(ev)
        self.redraw()

    def send_buttons(self, a=False, b=False, stick=False):
        ev = self.default_events()
        ev["a_pressed"] = a
        ev["b_pressed"] = b
        ev["stick_pressed"] = stick
        self.sim.handle_input(ev)
        self.redraw()

    def set_scene(self, scene):
        self.sim.scene = scene
        self.sim.cursor = 0
        if scene == "recruit" and self.sim.roster:
            self.sim.selected_recruit_id = self.sim.roster[0]["id"]
        self.redraw()

    def redraw(self):
        self.sim.render()
        self.canvas.delete("all")

        for op in self.sim.d.ops:
            kind = op[0]
            if kind == "fill":
                color = _rgb565_to_hex(op[1])
                self.canvas.create_rectangle(0, 0, 128 * self.SCALE, 160 * self.SCALE, outline="", fill=color)
            elif kind == "fill_rect":
                _, x, y, w, h, c = op
                color = _rgb565_to_hex(c)
                self.canvas.create_rectangle(
                    x * self.SCALE,
                    y * self.SCALE,
                    (x + w) * self.SCALE,
                    (y + h) * self.SCALE,
                    outline="",
                    fill=color,
                )
            elif kind == "rect":
                _, x, y, w, h, c = op
                color = _rgb565_to_hex(c)
                self.canvas.create_rectangle(
                    x * self.SCALE,
                    y * self.SCALE,
                    (x + w) * self.SCALE,
                    (y + h) * self.SCALE,
                    outline=color,
                    width=1,
                )
            elif kind == "pixel":
                _, x, y, c = op
                color = _rgb565_to_hex(c)
                self.canvas.create_rectangle(
                    x * self.SCALE,
                    y * self.SCALE,
                    (x + 1) * self.SCALE,
                    (y + 1) * self.SCALE,
                    outline="",
                    fill=color,
                )
            elif kind == "text":
                _, txt, x, y, c = op
                color = _rgb565_to_hex(c)
                self.canvas.create_text(
                    x * self.SCALE,
                    y * self.SCALE,
                    anchor="nw",
                    text=txt,
                    fill=color,
                    font=("Consolas", 7 * self.SCALE // 2),
                )

        self.root.update_idletasks()

    def run(self):
        self.root.mainloop()


def main():
    ScenePreview().run()


if __name__ == "__main__":
    main()
