import os

from bmp24_stream import BMP24Reader, rgb565


ASSET_ROOTS = ("/sd/assets", "assets")
SCENE_BG = {
    # Internal guild/building scenes.
    "save_slots": "save_slots.bmp",
    "dashboard": "guild_hall.bmp",
    "roster": "roster.bmp",
    "tavern": "tavern.bmp",
    "recruit": "recruit.bmp",
    "training": "training.bmp",
    "settings": "settings.bmp",
    "log": "log.bmp",
    # Outside combat area uses corrupted tiles.
    "missions": "corrupted_tiles.bmp",
}
BG_DIRS = (
    "runtime/backgrounds",
    "backgrounds",
    "Backgrounds",
    "sprites/backgrounds",
    "sprites/Backgrounds",
)
RECRUIT_DIRS = (
    "runtime/recruits",
    "recruits",
    "sprites/recruits",
    "Characters",
    "characters",
    "sprites/characters",
    "sprites/Characters",
)
ENEMY_DIRS = (
    "runtime/enemies",
    "enemies",
    "Enemies",
    "sprites/enemies",
)
UI_ICON_DIRS = (
    "runtime/icons",
    "icons",
    "Icons",
    "ui/icons",
    "UI/icons",
)

MISSION_ENEMY_MAP = {
    "goblin_cave_raid": "enemy_01.bmp",
    "escort_the_merchant": "enemy_02.bmp",
    "lost_relic_recovery": "enemy_03.bmp",
    "haunted_crypt": "enemy_04.bmp",
    "dragon_s_outpost": "enemy_05.bmp",
    "wyvern_hunt": "enemy_06.bmp",
    "demon_gate": "enemy_07.bmp",
    "shadow_lord_s_keep": "enemy_08.bmp",
    "herb_gathering": "enemy_09.bmp",
    "bandit_ambush": "enemy_10.bmp",
    "undead_siege": "enemy_11.bmp",
    "ancient_dungeon": "enemy_12.bmp",
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


def _slug(text):
    out = []
    prev_us = False
    for ch in text.lower():
        is_word = ("a" <= ch <= "z") or ("0" <= ch <= "9")
        if is_word:
            out.append(ch)
            prev_us = False
        elif not prev_us:
            out.append("_")
            prev_us = True
    s = "".join(out).strip("_")
    return s or "unknown"


def _hash_text(text):
    h = 2166136261
    for ch in text:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return h


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
                        display.pixel(px, yy, rgb565(r, g, b))
                    px += 1
                    col += 1
        return True
    except Exception:
        return False


def draw_scene_background(display, scene):
    name = SCENE_BG.get(scene)
    if not name:
        return False
    for d in BG_DIRS:
        path = resolve_asset(d + "/" + name)
        if path and _draw_bmp(display, path, 0, 0, display.width, display.height):
            return True
    return False


def draw_recruit_asset(display, recruit, x, y):
    rid = recruit.get("id", "")
    job = recruit.get("job_class", "Recruit")
    race_name = recruit.get("race", "Human")
    jc = job.lower().replace(" ", "_")
    race = race_name.lower().replace(" ", "_")
    uniq = _hash_text(rid or recruit.get("name", "recruit")) % 64

    names = (
        rid + ".bmp",
        "char_%02d.bmp" % uniq,
        "class_" + jc + ".bmp",
        "class_" + job + ".bmp",
        "race_" + race + ".bmp",
        "race_" + race_name + ".bmp",
        "default.bmp",
    )

    for d in RECRUIT_DIRS:
        for name in names:
            path = resolve_asset(d + "/" + name)
            if path and _draw_bmp(display, path, x, y, 16, 24):
                return True
    return False


def draw_enemy_asset(display, mission, x, y, w=28, h=28):
    mname = mission.get("name", "enemy")
    diff = int(mission.get("difficulty", 1))
    slug = _slug(mname)

    # Testing shortcut: when only one enemy is available, skip mission mapping.
    has_enemy_01 = False
    has_enemy_02 = False
    for d in ENEMY_DIRS:
        if resolve_asset(d + "/enemy_01.bmp"):
            has_enemy_01 = True
        if resolve_asset(d + "/enemy_02.bmp"):
            has_enemy_02 = True
    if has_enemy_01 and not has_enemy_02:
        names = ("enemy_01.bmp", "default.bmp")
    else:
        mapped_enemy = MISSION_ENEMY_MAP.get(slug)
        names = (
            "mission_" + slug + ".bmp",
            mapped_enemy if mapped_enemy else "",
            "difficulty_" + str(diff) + ".bmp",
            "enemy_" + str(diff) + ".bmp",
            "enemy_%02d.bmp" % ((_hash_text(mname) % 12) + 1),
            "default.bmp",
        )

    for d in ENEMY_DIRS:
        for name in names:
            if not name:
                continue
            path = resolve_asset(d + "/" + name)
            if path and _draw_bmp(display, path, x, y, w, h):
                return True
    return False


def draw_ui_icon(display, icon_name, x, y, w=8, h=8):
    slug = _slug(icon_name)
    names = (slug + ".bmp", icon_name + ".bmp", "default.bmp")
    for d in UI_ICON_DIRS:
        for name in names:
            path = resolve_asset(d + "/" + name)
            if path and _draw_bmp(display, path, x, y, w, h):
                return True
    return False
