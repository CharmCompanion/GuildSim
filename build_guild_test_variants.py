from __future__ import annotations

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT / "assets" / "scenes" / "Guild"
OUT_DIR = ROOT / "assets" / "runtime" / "backgrounds"
# Match active framebuffer dimensions in st7735_1inch8.py.
SIZE = (160, 128)
BG = (10, 12, 16)

SOURCES = [
    ("Guild1.1.png", "guild_test_fit_1_1.bmp"),
]


def flatten_rgba(img: Image.Image) -> Image.Image:
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    canvas = Image.new("RGB", img.size, BG)
    canvas.paste(img, mask=img.split()[-1])
    return canvas


def trim_transparent_edges(img: Image.Image) -> Image.Image:
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    alpha = img.split()[-1]
    bbox = alpha.getbbox()
    if not bbox:
        return img
    return img.crop(bbox)


def cover_center_no_stretch(src: Image.Image) -> Image.Image:
    canvas = Image.new("RGB", SIZE, BG)
    sw, sh = src.size
    tw, th = SIZE
    if sw <= 0 or sh <= 0:
        return canvas

    # Full-bleed: scale to cover the whole screen, then center-crop.
    scale = max(tw / sw, th / sh)
    nw = max(1, int(sw * scale))
    nh = max(1, int(sh * scale))
    fitted = src.resize((nw, nh), Image.Resampling.LANCZOS)
    x = (nw - tw) // 2
    y = (nh - th) // 2
    canvas.paste(fitted.crop((x, y, x + tw, y + th)), (0, 0))
    return canvas


def rotate_90_clockwise(src: Image.Image) -> Image.Image:
    return src.transpose(Image.Transpose.ROTATE_270)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for src_name, out_name in SOURCES:
        src_path = SRC_DIR / src_name
        if not src_path.exists():
            print(f"Missing source: {src_path}")
            continue

        img = Image.open(src_path).convert("RGBA")
        img = trim_transparent_edges(img)
        img = flatten_rgba(img)
        img = rotate_90_clockwise(img)
        out = cover_center_no_stretch(img)

        out_path = OUT_DIR / out_name
        out.save(out_path, format="BMP")
        written.append(out_path)
        print(f"Wrote {out_path}")

    print(f"Done. Generated {len(written)} fitted guild test BMPs.")


if __name__ == "__main__":
    main()
