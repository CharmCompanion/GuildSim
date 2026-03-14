from __future__ import annotations

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT / "assets" / "scenes" / "Guild"
OUT_DIR = ROOT / "assets" / "runtime" / "backgrounds"

SIZE = (160, 128)
CELL = 4
ROTATE_CW = True
BG_COLOR = (10, 12, 16)
FG_KEY = (255, 0, 255)  # Chroma key for foreground occluder transparency on Pico.

SRC_BG = SRC_DIR / "GuildBG.png"
SRC_FG = SRC_DIR / "GuildFG.png"
SRC_WALK = SRC_DIR / "GuildWalk.png"

OUT_BG = OUT_DIR / "guild_scene_bg.bmp"
OUT_FG = OUT_DIR / "guild_scene_fg.bmp"
OUT_WALK = OUT_DIR / "guild_scene_walkmask.txt"


def _rotate(img: Image.Image) -> Image.Image:
    if not ROTATE_CW:
        return img
    return img.transpose(Image.Transpose.ROTATE_270)


def _cover_rgba(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    sw, sh = img.size
    tw, th = size
    if sw <= 0 or sh <= 0:
        return Image.new("RGBA", size, BG_COLOR + (255,))

    scale = max(tw / sw, th / sh)
    nw = max(1, int(sw * scale))
    nh = max(1, int(sh * scale))
    fitted = img.resize((nw, nh), Image.Resampling.LANCZOS)
    x = (nw - tw) // 2
    y = (nh - th) // 2
    return fitted.crop((x, y, x + tw, y + th))


def _build_bg() -> Image.Image:
    bg = Image.open(SRC_BG).convert("RGBA")
    bg = _rotate(bg)
    bg = _cover_rgba(bg, SIZE)
    canvas = Image.new("RGB", SIZE, BG_COLOR)
    canvas.paste(bg, mask=bg.split()[-1])
    return canvas


def _build_fg() -> Image.Image:
    fg = Image.open(SRC_FG).convert("RGBA")
    fg = _rotate(fg)
    fg = _cover_rgba(fg, SIZE)

    # Foreground is encoded with chroma key in RGB BMP to keep transparency semantics.
    canvas = Image.new("RGB", SIZE, FG_KEY)
    canvas.paste(fg, mask=fg.split()[-1])
    return canvas


def _build_walkmask() -> list[str]:
    walk = Image.open(SRC_WALK).convert("RGBA")
    walk = _rotate(walk)
    walk = _cover_rgba(walk, SIZE)

    px = walk.load()
    w, h = SIZE
    cols = w // CELL
    rows = h // CELL

    lines: list[str] = []
    for gy in range(rows):
        row_bits = []
        for gx in range(cols):
            x0 = gx * CELL
            y0 = gy * CELL

            blocked = 0
            total = 0
            for yy in range(y0, y0 + CELL):
                for xx in range(x0, x0 + CELL):
                    r, g, b, a = px[xx, yy]
                    total += 1
                    if a > 0 and r < 30 and g < 30 and b < 30:
                        blocked += 1

            # If at least 25% of a cell is blocked by black walk layer, mark non-walkable.
            walkable = 0 if blocked * 4 >= total else 1
            row_bits.append(str(walkable))
        lines.append("".join(row_bits))
    return lines


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    bg = _build_bg()
    fg = _build_fg()
    mask_lines = _build_walkmask()

    bg.save(OUT_BG, format="BMP")
    fg.save(OUT_FG, format="BMP")

    header = [f"SIZE={SIZE[0]}x{SIZE[1]}", f"CELL={CELL}", f"COLS={SIZE[0] // CELL}", f"ROWS={SIZE[1] // CELL}"]
    OUT_WALK.write_text("\n".join(header + mask_lines) + "\n", encoding="ascii")

    print(f"Wrote {OUT_BG}")
    print(f"Wrote {OUT_FG}")
    print(f"Wrote {OUT_WALK}")


if __name__ == "__main__":
    main()
