from __future__ import annotations

from pathlib import Path
import random

from PIL import Image


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "assets" / "scenes" / "Guild"
OUT = ROOT / "assets" / "runtime" / "backgrounds"
SPRITE_SRC = ROOT / "static" / "sprites" / "characters" / "1x_-_Full_spritesheet_(16x24).png"
SPRITE_CLOTHING_DIR = ROOT / "static" / "sprites" / "characters" / "clothing"
SPRITE_HAIR_DIR = ROOT / "static" / "sprites" / "characters" / "hair"
SPRITE_FACE_DIR = ROOT / "static" / "sprites" / "characters" / "faces"
SPRITE_OUT_DIR = ROOT / "assets" / "runtime" / "sprites"

# Match active display/framebuffer profile — portrait 128×160.
SIZE = (128, 160)
ROTATE_CW = False

SOURCES = [
    ("GuildBG.png", "guild_preview_bg.bmp"),
    ("GuildFG.png", "guild_preview_fg.bmp"),
    ("GuildWalk.png", "guild_preview_walk.bmp"),
]

OUT_COMPOSITE = OUT / "guild_preview_comp.bmp"
FG_KEY = (255, 0, 255)
SPRITE_FRAME_SIZE = (16, 24)
SPRITE_SCALE = 2
SPRITE_KEY = (255, 0, 255)
SPRITE_ROW = 0
SPRITE_COLS = (0, 1, 2, 3)
PARTY_SIZE = 4

SKIN_TONES = (
    ((198, 136, 112), (170, 112, 92)),
    ((182, 124, 98), (154, 100, 80)),
    ((166, 108, 84), (138, 86, 68)),
    ((150, 96, 74), (124, 74, 58)),
    ((134, 84, 66), (110, 64, 50)),
)


def rotate_if_needed(img: Image.Image) -> Image.Image:
    if not ROTATE_CW:
        return img
    return img.transpose(Image.Transpose.ROTATE_270)


def cover_crop(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    sw, sh = img.size
    tw, th = size
    if sw <= 0 or sh <= 0:
        mode = "RGBA" if img.mode == "RGBA" else "RGB"
        fill = (0, 0, 0, 0) if mode == "RGBA" else (0, 0, 0)
        return Image.new(mode, size, fill)

    scale = max(tw / sw, th / sh)
    nw = max(1, int(sw * scale))
    nh = max(1, int(sh * scale))
    resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
    x = (nw - tw) // 2
    y = (nh - th) // 2
    return resized.crop((x, y, x + tw, y + th))


def flatten_rgba(img: Image.Image, bg=(0, 0, 0)) -> Image.Image:
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    canvas = Image.new("RGB", img.size, bg)
    canvas.paste(img, mask=img.split()[-1])
    return canvas


def chroma_from_rgba(img: Image.Image, key=FG_KEY) -> Image.Image:
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    # Hard-key transparency so antialiasing does not blend into magenta,
    # which creates visible purple fringes on the panel.
    out = Image.new("RGB", img.size, key)
    src = img.load()
    dst = out.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = src[x, y]
            if a >= 128:
                dst[x, y] = (r, g, b)
    return out


def export_party_frames() -> int:
    SPRITE_OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not SPRITE_SRC.exists():
        print(f"Missing sprite sheet: {SPRITE_SRC}")
        return 0

    body_sheet = Image.open(SPRITE_SRC).convert("RGBA")
    clothing_paths = sorted(SPRITE_CLOTHING_DIR.glob("Small*_walk.png"))
    hair_paths = sorted(SPRITE_HAIR_DIR.glob("Small*_walk.png"))
    face_paths = sorted(SPRITE_FACE_DIR.glob("Small*_walk.png"))

    if not clothing_paths:
        print(f"No clothing layers found in: {SPRITE_CLOTHING_DIR}")
        return 0
    if not hair_paths:
        print(f"No hair layers found in: {SPRITE_HAIR_DIR}")
        return 0
    if not face_paths:
        print(f"No face layers found in: {SPRITE_FACE_DIR}")
        return 0

    rng = random.Random()

    # Prefer unique outfits within the party, then randomize hair/face.
    rng.shuffle(clothing_paths)
    chosen_clothing = clothing_paths[:PARTY_SIZE]
    while len(chosen_clothing) < PARTY_SIZE:
        chosen_clothing.append(rng.choice(clothing_paths))

    members = []
    for idx in range(PARTY_SIZE):
        clothing_path = chosen_clothing[idx]
        hair_path = rng.choice(hair_paths)
        face_path = rng.choice(face_paths)
        skin_light, skin_mid = rng.choice(SKIN_TONES)
        members.append(
            {
                "id": idx,
                "clothing_name": clothing_path.name,
                "hair_name": hair_path.name,
                "face_name": face_path.name,
                "skin_light": skin_light,
                "skin_mid": skin_mid,
                "clothing": Image.open(clothing_path).convert("RGBA"),
                "hair": Image.open(hair_path).convert("RGBA"),
                "face": Image.open(face_path).convert("RGBA"),
            }
        )

    print("Party layer picks:")
    for m in members:
        print(
            f"  adv{m['id']}: clothing={m['clothing_name']}  "
            f"hair={m['hair_name']}  face={m['face_name']}  "
            f"skin={m['skin_light']}/{m['skin_mid']}"
        )

    fw, fh = SPRITE_FRAME_SIZE
    count = 0

    for member in members:
        for i, col in enumerate(SPRITE_COLS):
            left = col * fw
            top = SPRITE_ROW * fh
            frame = body_sheet.crop((left, top, left + fw, top + fh))

            # Composite ordered layers on top of body.
            cloth_frame = member["clothing"].crop((left, 0, left + fw, fh))
            hair_frame = member["hair"].crop((left, 0, left + fw, fh))
            face_frame = member["face"].crop((left, 0, left + fw, fh))
            frame.paste(cloth_frame, (0, 0), mask=cloth_frame.split()[-1])
            frame.paste(hair_frame, (0, 0), mask=hair_frame.split()[-1])
            frame.paste(face_frame, (0, 0), mask=face_frame.split()[-1])

            if SPRITE_SCALE > 1:
                frame = frame.resize(
                    (fw * SPRITE_SCALE, fh * SPRITE_SCALE),
                    Image.Resampling.NEAREST,
                )

            # Display is now portrait — sprite is already upright, no rotation needed.
            # Export as raw RGB565 little-endian for keyed software blit on Pico.
            w, h = frame.size
            pix = frame.load()
            raw = bytearray(w * h * 2)
            CHROMA = 0xF81F
            for fy in range(h):
                for fx in range(w):
                    r, g, b, a = pix[fx, fy]
                    if a < 220 or (r > 210 and g < 95 and b > 210):
                        c = CHROMA
                    else:
                        # Randomized natural skin tones per adventurer.
                        if r > 155 and g > 110 and b > 85:
                            r, g, b = member["skin_light"]
                        elif r > 120 and g > 70 and b > 55 and r >= g >= b:
                            r, g, b = member["skin_mid"]

                        c = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                        if c == CHROMA:
                            c = 0xF8FF  # prevent accidental key collision
                    pidx = (fy * w + fx) * 2
                    raw[pidx] = c & 0xFF
                    raw[pidx + 1] = c >> 8

            out_path = SPRITE_OUT_DIR / f"adv{member['id']}_f{i}.bin"
            out_path.write_bytes(raw)
            print(f"Wrote {out_path}  ({w}x{h})")
            count += 1

    return count


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    count = 0
    comp_bg = None
    comp_fg = None

    sprite_count = export_party_frames()

    for src_name, out_name in SOURCES:
        src_path = SRC / src_name
        if not src_path.exists():
            print(f"Missing: {src_path}")
            continue

        src_rgba = Image.open(src_path).convert("RGBA")
        src_rgba = rotate_if_needed(src_rgba)
        fitted_rgba = cover_crop(src_rgba, SIZE).convert("RGBA")

        if src_name == "GuildBG.png":
            out = flatten_rgba(fitted_rgba, (0, 0, 0))
            comp_bg = fitted_rgba
        elif src_name == "GuildFG.png":
            out = chroma_from_rgba(fitted_rgba, FG_KEY)
            comp_fg = fitted_rgba
        else:
            out = flatten_rgba(fitted_rgba, (0, 0, 0))

        out_path = OUT / out_name
        out.save(out_path, format="BMP")
        print(f"Wrote {out_path}")
        count += 1

    if comp_bg is not None:
        scene = Image.new("RGBA", SIZE, (0, 0, 0, 255))
        scene.alpha_composite(comp_bg)
        if comp_fg is not None:
            scene.alpha_composite(comp_fg)
        scene.convert("RGB").save(OUT_COMPOSITE, format="BMP")
        print(f"Wrote {OUT_COMPOSITE}")

    print(f"Done. Generated {count} preview BMPs and {sprite_count} party sprite frames.")


if __name__ == "__main__":
    main()
