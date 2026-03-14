from machine import Pin, PWM  # pyright: ignore[reportMissingImports]
import random
import time

import lcd
from bmp24_stream import BMP24Reader
from pico_sprites import draw_recruit


BG_PATH = "/images/guild_scene_bg.bmp"
MASK_PATH = "/images/guild_scene_walkmask.txt"
PARTY_COUNT = 2


def color565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def draw_bmp(display, path):
    with open(path, "rb") as f:
        reader = BMP24Reader(f)
        w = min(reader.width, display.width)
        h = min(reader.height, display.height)
        x_off = (display.width - w) // 2
        y_off = (display.height - h) // 2

        for y in range(h):
            x = x_off
            for r, g, b in reader.iter_pixels(y):
                if x >= x_off + w:
                    break
                display.pixel(x, y + y_off, color565(r, g, b))
                x += 1


def load_walkmask(path):
    with open(path, "r") as f:
        lines = [ln.strip() for ln in f if ln.strip()]

    meta = {}
    grid = []
    for ln in lines:
        if "=" in ln and not set(ln).issubset({"0", "1"}):
            k, v = ln.split("=", 1)
            meta[k] = v
        elif set(ln).issubset({"0", "1"}):
            grid.append(ln)

    cell = int(meta.get("CELL", "4"))
    cols = int(meta.get("COLS", str(len(grid[0]) if grid else 0)))
    rows = int(meta.get("ROWS", str(len(grid))))
    return cell, cols, rows, grid


def walkable(grid, gx, gy):
    if gy < 0 or gy >= len(grid):
        return False
    row = grid[gy]
    if gx < 0 or gx >= len(row):
        return False
    return row[gx] == "1"


def make_party(count):
    jobs = ["Warrior", "Mage", "Ranger", "Knight", "Assassin", "Paladin", "Necromancer"]
    party = []
    for i in range(count):
        party.append(
            {
                "id": "adv_" + str(i),
                "name": "Adv" + str(i),
                "job_class": random.choice(jobs),
                "gx": 0,
                "gy": 0,
            }
        )
    return party


def place_party(party, grid):
    cells = []
    for gy, row in enumerate(grid):
        for gx, bit in enumerate(row):
            if bit == "1":
                cells.append((gx, gy))
    random.shuffle(cells)
    for i, p in enumerate(party):
        if i < len(cells):
            p["gx"], p["gy"] = cells[i]


def step_agent(agent, grid):
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    random.shuffle(dirs)
    gx, gy = agent["gx"], agent["gy"]
    for dx, dy in dirs:
        nx, ny = gx + dx, gy + dy
        if walkable(grid, nx, ny):
            agent["gx"], agent["gy"] = nx, ny
            return


def main():
    bl = PWM(Pin(13))
    bl.freq(1000)
    bl.duty_u16(0)

    d = lcd.LCD_1inch8()

    cell, cols, rows, grid = load_walkmask(MASK_PATH)
    party = make_party(PARTY_COUNT)
    place_party(party, grid)

    bl.duty_u16(56000)

    tick = 0
    while True:
        d.fill(0x0000)
        draw_bmp(d, BG_PATH)

        # Move less often to reduce full-screen redraw pressure.
        if tick % 4 == 0:
            for p in party:
                step_agent(p, grid)

        for p in party:
            px = p["gx"] * cell
            py = p["gy"] * cell
            draw_recruit(d, px, py, p, scale=1)

        d.show()

        tick += 1
        time.sleep_ms(360)


if __name__ == "__main__":
    main()
