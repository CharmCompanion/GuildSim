from machine import Pin, PWM  # pyright: ignore[reportMissingImports]
import time
import random
import gc

import lcd
from bmp24_stream import BMP24Reader

# ── constants ─────────────────────────────────────────────────────────────────
BG_IMAGE_PATH = "/images/guild_preview_bg.bmp"
FG_IMAGE_PATH = "/images/guild_preview_fg.bmp"
SPRITE_W      = 32   # portrait display: sprite stands upright 32×48
SPRITE_H      = 48
NUM_FRAMES    = 4
PARTY_SIZE    = 4
PARTY_LITE_MODE = True
SAFE_BOOT_SPLASH = True
CHROMA        = 0xF81F   # magenta chroma key for blit()
PARTY_NAMES   = ("KNOX", "RHEA", "MILO", "TESS")
SPRITE_TAG    = "S28"

# ── helpers ───────────────────────────────────────────────────────────────────
def color565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def panel_tone_fix(r, g, b):
    # Global darkening for scene layers so highlights don't blow out on panel.
    r = (r * 165) // 255
    g = (g * 160) // 255
    b = (b * 165) // 255

    # This panel clips neutral highlights; aggressively compress near-greys.
    dr = abs(r - g)
    dg = abs(g - b)
    db = abs(r - b)
    if dr < 22 and dg < 22 and db < 22:
        m = (r + g + b) // 3
        if m > 140:
            r = (r * 120) // 255
            g = (g * 120) // 255
            b = (b * 120) // 255
        elif m > 100:
            r = (r * 145) // 255
            g = (g * 145) // 255
            b = (b * 145) // 255
    return r, g, b


def _stream_bmp(display, path, skip_chroma=False):
    """Draw one BMP into display buffer. If skip_chroma, skip magenta pixels."""
    with open(path, "rb") as f:
        reader = BMP24Reader(f)
        w = min(reader.width, display.width)
        h = min(reader.height, display.height)
        x_off = (display.width  - w) // 2
        y_off = (display.height - h) // 2
        for row in range(h):
            col = x_off
            for r, g, b in reader.iter_pixels(row):
                if col >= x_off + w:
                    break
                # Skip exact and near-magenta to remove fringe pixels.
                if skip_chroma and ((r > 220 and g < 90 and b > 220) or (r > 180 and g < 70 and b > 180)):
                    col += 1
                    continue
                r, g, b = panel_tone_fix(r, g, b)
                c = color565(r, g, b)
                if not (skip_chroma and c == CHROMA):
                    display.pixel(col, row + y_off, c)
                col += 1


def load_scene_snapshot(display, bg_path, fg_path):
    """Composite BG then FG into display buffer; snapshot into one bytearray.
    Uses only one extra 40 KB allocation instead of two — safe on a Pico."""
    display.fill(0)
    _stream_bmp(display, bg_path)
    try:
        _stream_bmp(display, fg_path, skip_chroma=True)
    except Exception as e:
        print("FG overlay skipped:", e)
    return bytearray(display.buffer)


def load_sprite_framebuf(path):
    """Load raw RGB565 .bin into a bytearray (little-endian RGB565)."""
    buf = bytearray(SPRITE_W * SPRITE_H * 2)
    with open(path, "rb") as f:
        f.readinto(buf)
    sanitize_sprite_buf(buf)
    return buf


def sanitize_sprite_buf(buf):
    """Panel-side fixup: drop magenta fringe and restore skin/hair visibility."""
    for i in range(0, len(buf), 2):
        c = buf[i] | (buf[i + 1] << 8)
        if c == CHROMA:
            continue

        r = ((c >> 11) & 0x1F) * 255 // 31
        g = ((c >> 5) & 0x3F) * 255 // 63
        b = (c & 0x1F) * 255 // 31

        # Remove pink fringe fragments that survived export.
        if r > 180 and g < 95 and b > 170:
            c2 = CHROMA
        else:
            # Mild global compensation; keep generated palette relationships intact.
            r = (r * 210) // 255
            g = (g * 205) // 255
            b = (b * 210) // 255

            # Panel clips neutral highlights; compress only near-greys.
            dr = abs(r - g)
            dg = abs(g - b)
            db = abs(r - b)
            if dr < 18 and dg < 18 and db < 18:
                m = (r + g + b) // 3
                if m > 150:
                    r = (r * 130) // 255
                    g = (g * 130) // 255
                    b = (b * 130) // 255

            c2 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            if c2 == CHROMA:
                c2 = 0xF8FF

        buf[i] = c2 & 0xFF
        buf[i + 1] = (c2 >> 8) & 0xFF


def blit_sprite_keyed(display, src_buf, dx, dy, sw, sh, key):
    """Software keyed blit into display.buffer to avoid framebuf key quirks."""
    dw = display.width
    dh = display.height
    dst = display.buffer

    for sy in range(sh):
        ty = dy + sy
        if ty < 0 or ty >= dh:
            continue
        src_row = sy * sw * 2
        dst_row = ty * dw * 2
        for sx in range(sw):
            tx = dx + sx
            if tx < 0 or tx >= dw:
                continue
            si = src_row + sx * 2
            c = src_buf[si] | (src_buf[si + 1] << 8)
            if c == key:
                continue
            di = dst_row + tx * 2
            dst[di] = src_buf[si]
            dst[di + 1] = src_buf[si + 1]


def shadow_text(display, x, y, text, color):
    """Readable text with a 1-px black shadow — no opaque background box."""
    display.text(text, x + 1, y + 1, 0x0000)
    display.text(text, x,     y,     color)


def draw_labels(display, sx, sy, name, rank):
    """Draw name and role centered above sprite head, no opaque background box."""
    sw = SPRITE_W
    name_w = len(name) * 8
    rank_w = len(rank) * 8
    cx = sx + sw // 2
    nx = max(0, min(display.width - name_w, cx - name_w // 2))
    rx = max(0, min(display.width - rank_w, cx - rank_w // 2))
    # Name 14px above sprite top, rank 6px above sprite top.
    shadow_text(display, nx, max(1, sy - 14), name, 0xFFE0)  # yellow
    shadow_text(display, rx, max(9, sy - 6),  rank, 0xBDF7)  # light blue


def make_party_lite_background(display):
    """Build a cheap reusable background buffer for low-RAM party mode."""
    display.fill(0x10A2)  # deep slate-blue

    # Simple panel dividers so party slots are readable on plain background.
    display.hline(0, 78, display.width, 0x2965)
    display.vline(63, 0, display.height, 0x2965)

    # Minimal title strip.
    display.fill_rect(0, 0, display.width, 10, 0x0861)
    display.text("PARTY", 44, 1, 0xFFFF)
    return bytearray(display.buffer)


# ── main ──────────────────────────────────────────────────────────────────────
def main():
    bl = PWM(Pin(13))
    bl.freq(1000)
    bl.duty_u16(52000)

    d = lcd.LCD_1inch8()

    if SAFE_BOOT_SPLASH:
        d.fill(0xF800)  # red flash proves script is alive
        d.show()
        time.sleep_ms(200)
        d.fill(0x07E0)  # green flash confirms panel updates
        d.show()
        time.sleep_ms(200)

    d.fill(0x0000)
    d.text("LOADING", 34, 68, 0xFFFF)
    d.show()

    if PARTY_LITE_MODE:
        print("Loading party-lite background...")
        bg_buf = make_party_lite_background(d)
    else:
        try:
            print("Loading scene (BG+FG)...")
            bg_buf = load_scene_snapshot(d, BG_IMAGE_PATH, FG_IMAGE_PATH)
        except Exception as e:
            d.fill(0x0000)
            d.text("LOAD FAIL", 16, 66, 0xF800)
            d.show()
            print("Scene load error:", e)
            while True:
                time.sleep_ms(500)

    print("Loading party sprites...")
    party_sprites = []
    for member in range(PARTY_SIZE):
        try:
            # Low-RAM path: pick one random walk frame per adventurer.
            fidx = random.randint(0, NUM_FRAMES - 1)
            path = "/images/adv{}_f{}.bin".format(member, fidx)
            buf = load_sprite_framebuf(path)
            party_sprites.append(buf)
        except Exception as e:
            print("Party frame load fail", member, e)

    # Backward-compatible fallback if adv files are missing.
    if not party_sprites:
        try:
            party_sprites.append(load_sprite_framebuf("/images/knox_f0.bin"))
        except Exception as e:
            print("Fallback frame load fail", e)

    gc.collect()

    if not party_sprites:
        d.fill(0x0000)
        d.text("SPRITE FAIL", 14, 66, 0xF800)
        d.show()
        while True:
            time.sleep_ms(500)

    bl.duty_u16(56000)
    print("Running — fast blit loop")

    # ── party layout and animation state ──────────────────────────────────────
    party_slots = [
        (6, 48),
        (90, 48),
        (6, 106),
        (90, 106),
    ]
    while True:
        # ── render (NO file I/O — pure memory operations) ──────────────────────
        d.buffer[:] = bg_buf[:]  # BG+FG composite

        for idx, member_buf in enumerate(party_sprites):
            if idx >= len(party_slots):
                break

            sx, sy = party_slots[idx]
            # Small idle bob and frame offset keeps the party alive without overlap.
            bob = ((time.ticks_ms() // 300) + idx) & 1
            fy = sy - bob
            blit_sprite_keyed(d, member_buf, sx, fy, SPRITE_W, SPRITE_H, CHROMA)

            # Keep text light to reduce per-frame overhead.
            name = PARTY_NAMES[idx % len(PARTY_NAMES)]
            shadow_text(d, sx, max(0, fy - 10), name, 0xFFE0)

        d.text(SPRITE_TAG, 1, 1, 0x07E0)

        d.show()
        time.sleep_ms(140)


if __name__ == "__main__":
    main()
