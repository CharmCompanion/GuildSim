# Pico Flash vs SD Card Split

This project is staged to support a strict deployment split.

## Copy To Pico Internal Flash (required runtime)

- `main.py`
- `guild_sim_main.py`
- `pico_app.py`
- `pico_input.py`
- `pico_sprites.py`
- `models.py`
- `lcd.py`
- `st7735_1inch8.py`

Optional runtime data folder:
- `saves/` (if you want existing slots preloaded)

## Keep On SD Card (optional / non-runtime)

- `assets/runtime/` (prepared 24-bit BMP runtime art)
- `static/` (legacy art and web-era assets)
- `templates/` (legacy web templates)
- `Old/` (archive of previous iterations and test scripts)
- `attached_assets/`
- docs and deployment scripts not needed by firmware runtime

## Why This Split

The runtime does not import `static`, `templates`, or `Old`. Keeping those on SD avoids filling Pico flash.

## Recommended On-Device Layout

Pico flash root:
- runtime files above
- `saves/` (if local save persistence desired)

SD root:
- `/assets/runtime` (required for full art-driven Pico UI)
- `/assets` (optional full source packs archive)
- `/archive` (copy from `Old/`)

## Asset Preparation

Before deploying art packs to SD, generate runtime BMP assets:
1. `pip install pillow`
2. `python prepare_pico_assets.py`
3. copy `assets/runtime` to `/sd/assets/runtime`
