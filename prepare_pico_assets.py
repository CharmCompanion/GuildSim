"""Build Pico-ready BMP runtime assets from source packs.

This converts selected PNG art into 24-bit BMP files used by the MicroPython
runtime. Output is written to assets/runtime/.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    from PIL import Image
except Exception:
    print("Pillow is required. Install with: pip install pillow")
    raise

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
OUT = ASSETS / "runtime"
LAYOUTS = ASSETS / "layouts"

SIZE_SCREEN = (128, 160)
SIZE_RECRUIT = (16, 24)
SIZE_ENEMY = (28, 24)
SIZE_ICON = (8, 8)

SCENE_NAMES = {
    "save_slots": "save_slots.bmp",
    "dashboard": "guild_hall.bmp",
    "roster": "roster.bmp",
    "tavern": "tavern.bmp",
    "recruit": "recruit.bmp",
    "training": "training.bmp",
    "settings": "settings.bmp",
    "log": "log.bmp",
    "missions": "corrupted_tiles.bmp",
}

MISSION_SLUGS = (
    "goblin_cave_raid",
    "escort_the_merchant",
    "lost_relic_recovery",
    "haunted_crypt",
    "dragon_s_outpost",
    "wyvern_hunt",
    "demon_gate",
    "shadow_lord_s_keep",
    "herb_gathering",
    "bandit_ambush",
    "undead_siege",
    "ancient_dungeon",
)


def ensure_dirs() -> None:
    for rel in ("backgrounds", "recruits", "enemies", "icons"):
        (OUT / rel).mkdir(parents=True, exist_ok=True)


def walk_png(base: Path) -> list[Path]:
    if not base.exists():
        return []
    files: list[Path] = []
    for p in base.rglob("*.png"):
        if p.is_file():
            files.append(p)
    return sorted(files)


def pick_by_keywords(paths: list[Path], includes: list[str], excludes: list[str] | None = None) -> list[Path]:
    excludes = excludes or []
    out: list[Path] = []
    for p in paths:
        s = str(p).lower()
        if all(k in s for k in includes) and not any(bad in s for bad in excludes):
            out.append(p)
    return out


def cover_resize(src: Image.Image, target_size: tuple[int, int]) -> Image.Image:
    tw, th = target_size
    sw, sh = src.size
    if sw <= 0 or sh <= 0:
        return Image.new("RGB", target_size, (10, 10, 14))
    scale = max(tw / sw, th / sh)
    nw = max(1, int(sw * scale))
    nh = max(1, int(sh * scale))
    img = src.resize((nw, nh), Image.Resampling.LANCZOS)
    x = (nw - tw) // 2
    y = (nh - th) // 2
    return img.crop((x, y, x + tw, y + th))


def open_rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def flatten_to_rgb(img: Image.Image, bg: tuple[int, int, int] = (10, 12, 16)) -> Image.Image:
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    canvas = Image.new("RGB", img.size, bg)
    canvas.paste(img, mask=img.split()[-1])
    return canvas


def save_bmp(img: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(path, format="BMP")


def _load_layout_scene(scene: str) -> Image.Image | None:
    layout_file = LAYOUTS / (scene + ".json")
    if not layout_file.exists():
        return None
    try:
        import json
        from PIL import ImageDraw, ImageFont

        payload = json.loads(layout_file.read_text(encoding="utf-8"))
        items = payload.get("items", [])
        bg = tuple(payload.get("bg", [10, 12, 16]))
        canvas = Image.new("RGBA", SIZE_SCREEN, bg)
        draw = ImageDraw.Draw(canvas)
        font = ImageFont.load_default()
        for item in items:
            kind = item.get("type", "sprite")
            x = int(item.get("x", 0))
            y = int(item.get("y", 0))
            w = int(item.get("w", 0))
            h = int(item.get("h", 0))
            if kind == "sprite":
                rel = item.get("path", "")
                if not rel:
                    continue
                src = (ASSETS / rel).resolve()
                if not src.exists():
                    continue
                sprite = open_rgba(src)
                sx = int(item.get("src_x", 0))
                sy = int(item.get("src_y", 0))
                sw = int(item.get("src_w", sprite.size[0]))
                sh = int(item.get("src_h", sprite.size[1]))
                if sx < 0:
                    sx = 0
                if sy < 0:
                    sy = 0
                if sw <= 0:
                    sw = 1
                if sh <= 0:
                    sh = 1
                if sx + sw > sprite.size[0]:
                    sw = max(1, sprite.size[0] - sx)
                if sy + sh > sprite.size[1]:
                    sh = max(1, sprite.size[1] - sy)
                sprite = sprite.crop((sx, sy, sx + sw, sy + sh))
                if w > 0 and h > 0:
                    sprite = sprite.resize((w, h), Image.Resampling.LANCZOS)
                canvas.alpha_composite(sprite, (x, y))
            elif kind == "text":
                color = item.get("color", "#ffffff")
                text = item.get("text", "Text")
                draw.text((x, y), text, fill=color, font=font)
            elif kind == "line":
                color = item.get("color", "#ffffff")
                stroke = max(1, int(item.get("stroke", 1)))
                x2 = int(item.get("x2", x + w))
                y2 = int(item.get("y2", y + h))
                draw.line((x, y, x2, y2), fill=color, width=stroke)
            elif kind == "rect":
                color = item.get("color", "#ffffff")
                stroke = max(1, int(item.get("stroke", 1)))
                draw.rectangle((x, y, x + w, y + h), outline=color, width=stroke)
            elif kind == "char_marker":
                draw.rectangle((x, y, x + w, y + h), outline="#22cc22", width=1)
            elif kind == "enemy_marker":
                draw.rectangle((x, y, x + w, y + h), outline="#ff3333", width=1)
        return canvas.convert("RGB")
    except Exception:
        return None


def build_backgrounds(all_png: list[Path]) -> None:
    ui_bg = pick_by_keywords(all_png, ["assets", "ui", "background boxes", "bgbox"])
    if len(ui_bg) < 8:
        ui_bg += pick_by_keywords(all_png, ["assets", "ui", "banner"])

    corrupted = pick_by_keywords(all_png, ["assets", "tilesets", "corrupted", "battle background"])
    if not corrupted:
        corrupted = pick_by_keywords(all_png, ["assets", "tilesets", "corrupted", "eldritchlandbg"])

    interior_defaults = ui_bg[:8]
    while len(interior_defaults) < 8:
        interior_defaults.append(None)  # type: ignore[arg-type]

    interior_scene_order = [
        "save_slots",
        "dashboard",
        "roster",
        "tavern",
        "recruit",
        "training",
        "settings",
        "log",
    ]

    for i, scene in enumerate(interior_scene_order):
        from_layout = _load_layout_scene(scene)
        if from_layout is not None:
            out = cover_resize(from_layout.convert("RGB"), SIZE_SCREEN)
        else:
            src = interior_defaults[i]
            if src:
                img = flatten_to_rgb(open_rgba(src), (14, 16, 20))
                out = cover_resize(img, SIZE_SCREEN)
            else:
                out = Image.new("RGB", SIZE_SCREEN, (20 + i * 3, 20 + i * 2, 28 + i * 2))
        save_bmp(out, OUT / "backgrounds" / SCENE_NAMES[scene])

    from_layout = _load_layout_scene("missions")
    if from_layout is not None:
        out = cover_resize(from_layout.convert("RGB"), SIZE_SCREEN)
    else:
        if corrupted:
            img = flatten_to_rgb(open_rgba(corrupted[0]), (10, 10, 16))
            out = cover_resize(img, SIZE_SCREEN)
        else:
            out = Image.new("RGB", SIZE_SCREEN, (34, 18, 24))
    save_bmp(out, OUT / "backgrounds" / SCENE_NAMES["missions"])


def build_recruits(all_png: list[Path]) -> None:
    chars = pick_by_keywords(all_png, ["assets", "characters", "_idle"], excludes=["walk", "face_"])
    if not chars:
        chars = pick_by_keywords(all_png, ["assets", "characters", "idle"])

    # Produce deterministic pool used by hash-based runtime selection: char_00..char_63.
    limit = min(64, len(chars))
    for i in range(limit):
        src = chars[i]
        img = flatten_to_rgb(open_rgba(src), (0, 0, 0))
        out = cover_resize(img, SIZE_RECRUIT)
        save_bmp(out, OUT / "recruits" / ("char_%02d.bmp" % i))

    # Class/race defaults for fallback routing.
    class_map = {
        "class_warrior.bmp": ["heavyarmor"],
        "class_knight.bmp": ["heavyarmor"],
        "class_paladin.bmp": ["robe", "heavyarmor"],
        "class_mage.bmp": ["robe"],
        "class_necromancer.bmp": ["robe"],
        "class_ranger.bmp": ["lightarmor"],
        "class_assassin.bmp": ["lightarmor"],
        "default.bmp": [],
    }

    for out_name, keys in class_map.items():
        src = None
        if keys:
            for k in keys:
                picks = [p for p in chars if k in p.name.lower()]
                if picks:
                    src = picks[0]
                    break
        if src is None and chars:
            src = chars[0]
        if src is None:
            img = Image.new("RGB", SIZE_RECRUIT, (60, 60, 60))
        else:
            img = cover_resize(flatten_to_rgb(open_rgba(src), (0, 0, 0)), SIZE_RECRUIT)
        save_bmp(img, OUT / "recruits" / out_name)


def build_enemies(all_png: list[Path]) -> None:
    enemies = pick_by_keywords(all_png, ["assets", "enemies", "front"])
    if not enemies:
        enemies = pick_by_keywords(all_png, ["assets", "enemies"])

    built_count = 0
    for i, src in enumerate(enemies[:12], start=1):
        img = flatten_to_rgb(open_rgba(src), (0, 0, 0))
        out = cover_resize(img, SIZE_ENEMY)
        save_bmp(out, OUT / "enemies" / ("enemy_%02d.bmp" % i))
        built_count += 1

    if built_count == 0:
        save_bmp(Image.new("RGB", SIZE_ENEMY, (120, 30, 40)), OUT / "enemies" / "enemy_01.bmp")
        built_count = 1

    # Final mode uses mission-specific names; each mission points to one prepared enemy slot.
    for i, slug in enumerate(MISSION_SLUGS):
        idx = (i % built_count) + 1
        src = OUT / "enemies" / ("enemy_%02d.bmp" % idx)
        save_bmp(Image.open(src).convert("RGB"), OUT / "enemies" / ("mission_" + slug + ".bmp"))

    for d in range(1, 6):
        idx = ((d - 1) % built_count) + 1
        src = OUT / "enemies" / ("enemy_%02d.bmp" % idx)
        if src.exists():
            save_bmp(Image.open(src).convert("RGB"), OUT / "enemies" / ("difficulty_%d.bmp" % d))

    default_src = OUT / "enemies" / "enemy_01.bmp"
    if default_src.exists():
        save_bmp(Image.open(default_src).convert("RGB"), OUT / "enemies" / "default.bmp")
    else:
        save_bmp(Image.new("RGB", SIZE_ENEMY, (120, 30, 40)), OUT / "enemies" / "default.bmp")


def build_icons(all_png: list[Path]) -> None:
    icon_pool = pick_by_keywords(all_png, ["assets", "icons"])
    role_to_idx = {
        "gold": 0,
        "party": 1,
        "mission": 2,
        "a": 3,
        "b": 4,
        "default": 5,
    }

    if not icon_pool:
        base = Image.new("RGB", SIZE_ICON, (220, 220, 220))
        for name in role_to_idx:
            save_bmp(base, OUT / "icons" / (name + ".bmp"))
        return

    for role, idx in role_to_idx.items():
        src = icon_pool[idx % len(icon_pool)]
        img = flatten_to_rgb(open_rgba(src), (0, 0, 0))
        out = cover_resize(img, SIZE_ICON)
        save_bmp(out, OUT / "icons" / (role + ".bmp"))


def write_manifest() -> None:
    lines = [
        "Pico runtime assets generated from source packs.",
        "",
        "backgrounds/",
        "- save_slots.bmp",
        "- guild_hall.bmp",
        "- roster.bmp",
        "- tavern.bmp",
        "- recruit.bmp",
        "- training.bmp",
        "- settings.bmp",
        "- log.bmp",
        "- corrupted_tiles.bmp",
        "",
        "recruits/",
        "- char_00.bmp .. char_63.bmp",
        "- class_*.bmp",
        "- default.bmp",
        "",
        "enemies/",
        "- enemy_01.bmp .. enemy_12.bmp",
        "- difficulty_1.bmp .. difficulty_5.bmp",
        "- default.bmp",
        "",
        "icons/",
        "- gold.bmp",
        "- party.bmp",
        "- mission.bmp",
        "- a.bmp",
        "- b.bmp",
        "- default.bmp",
    ]
    (OUT / "README.txt").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ensure_dirs()
    all_png = walk_png(ASSETS)
    if not all_png:
        print("No PNG files found under assets/.")
        return 1

    build_backgrounds(all_png)
    build_recruits(all_png)
    build_enemies(all_png)
    build_icons(all_png)
    write_manifest()

    print("Prepared Pico assets in:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
