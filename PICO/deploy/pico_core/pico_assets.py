import os

from bmp24_stream import BMP24Reader, rgb565


ASSET_ROOTS = ("/sd/assets", "assets")
SCENE_BG = {
    "save_slots": "backgrounds/save_slots.bmp",
    "dashboard": "backgrounds/guild_hall.bmp",
    "roster": "backgrounds/roster.bmp",
    "tavern": "backgrounds/tavern.bmp",
    "recruit": "backgrounds/recruit.bmp",
    "missions": "backgrounds/missions.bmp",
    "training": "backgrounds/training.bmp",
    "settings": "backgrounds/settings.bmp",
    "log": "backgrounds/log.bmp",
}


def _exists(path):
    try:
        os.stat(path)
        return True
    except OSError:
        return False


def _join(a, b):
    if a.endswith("/"):
        return a + b
    return a + "/" + b


def resolve_asset(rel_path):
    for root in ASSET_ROOTS:
        candidate = _join(root, rel_path)
        if _exists(candidate):
            return candidate
    return None


def _draw_bmp(display, abs_path, x=0, y=0, max_w=None, max_h=None):
    try:
        with open(abs_path, "rb") as fh:
            reader = BMP24Reader(fh)
            draw_w = reader.width if max_w is None else min(reader.width, max_w)
            draw_h = reader.height if max_h is None else min(reader.height, max_h)
            for row in range(draw_h):
                yy = y + row
                if yy < 0 or yy >= display.height:
                    continue
                px = x
                col = 0
                for r, g, b in reader.iter_pixels(row):
                    if col >= draw_w:
                        break
                    if 0 <= px < display.width:
                        # Panel-specific fix: this unit displays G/B swapped.
                        # Also nudge saturated blues toward neutral blue to reduce
                        # violet cast seen on this panel.
                        rr, gg, bb = r, g, b
                        if bb > 160 and rr < 100 and gg < 140:
                            rr = 0 if rr < 12 else rr - 12
                            gg = 255 if gg > 243 else gg + 12
                        display.pixel(px, yy, rgb565(rr, bb, gg))
                    px += 1
                    col += 1
        return True
    except Exception:
        return False


def draw_scene_background(display, scene):
    rel = SCENE_BG.get(scene)
    if not rel:
        return False
    path = resolve_asset(rel)
    if not path:
        return False
    return _draw_bmp(display, path, 0, 0, display.width, display.height)


def draw_recruit_asset(display, recruit, x, y):
    rid = recruit.get("id", "")
    jc = recruit.get("job_class", "Recruit").lower().replace(" ", "_")
    race = recruit.get("race", "Human").lower().replace(" ", "_")

    candidates = (
        "sprites/recruits/" + rid + ".bmp",
        "sprites/recruits/class_" + jc + ".bmp",
        "sprites/recruits/race_" + race + ".bmp",
        "sprites/recruits/default.bmp",
    )

    for rel in candidates:
        path = resolve_asset(rel)
        if path and _draw_bmp(display, path, x, y, 16, 24):
            return True
    return False
