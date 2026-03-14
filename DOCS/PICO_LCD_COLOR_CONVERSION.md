# Pico LCD 1.8 Color Conversion Notes

This document records the exact conversion/fix path that got correct colors on the Pico-LCD-1.8 (ST7735S) with MicroPython.

## Goal

- Fix wrong color mapping (pink showing as cyan/light blue, tan shifted, magenta wrong).
- Keep MicroPython workflow (not LVGL-only UF2 demo).
- Boot directly into a single image test (Chopper), not save slots.

## Known-Good Hardware Pin Map

- DIN -> GP11
- CLK -> GP10
- CS -> GP9
- DC -> GP8
- RST -> GP12
- BL -> GP13
- VCC -> 3V3/VSYS (per module wiring)
- GND -> GND

## Firmware Choice

Use MicroPython UF2 for Pico, not the LVGL demo UF2.

- LVGL UF2 can look correct, but it is not the same runtime as MicroPython scripts.
- Final setup keeps MicroPython firmware and applies display-driver fixes in code.

## What Was Fixed

### 1) Driver init and transmit behavior

File: st7735_1inch8.py

- Kept ST7735 1.8 init profile aligned with Waveshare 1.8 behavior.
- Added RGB565 byte-swap before SPI transmit (equivalent to LV_COLOR_16_SWAP=1 behavior).
- This was the key conversion step to correct channel interpretation on panel output.

### 2) Removed old color-hack remaps

Files:
- show_chopper_once.py
- show_uploaded_image_once.py
- pico_assets.py
- pico_sprites.py

- Removed legacy G/B swap and blue-trim compensation.
- Returned all image/sprite conversion to normal RGB565 packing.

### 3) Startup forced to image-only mode

Files:
- main.py
- guild_sim_main.py

- Startup now runs show_uploaded_image_once.main().
- Prevents app menu/save slots from appearing during image validation.

## Deployment Script

File: deploy_micropython_lcd18.ps1

Use from PowerShell in repo root:

```powershell
.\deploy_micropython_lcd18.ps1 -Port COM3
```

If PowerShell says script not found, use .\ prefix exactly.

## Storage Notes

If copy fails with "No space left on device":

1. Delete extra test BMP files from /images on Pico.
2. Re-copy required image:

```powershell
mpremote connect COM3 fs cp --force chopper_160x128.bmp :images/chopper_160x128.bmp
```

## Quick Verify Commands

```powershell
mpremote connect COM3 exec "import show_uploaded_image_once; show_uploaded_image_once.main()"
mpremote connect COM3 exec "import machine; machine.soft_reset()"
```

Expected run message:

- Displayed /images/chopper_160x128.bmp panel_fix=RGB565_NORMAL

## If COM Port Is Busy

- Close Thonny/serial monitor/other terminals using COM3.
- Unplug/replug Pico.
- Re-run deployment command.

## Optional Future ESP32-S3 Migration (Not Done Yet)

To move this display to ESP32-S3 later:

- Solder female jumper leads to LCD pins.
- Wire SPI + control lines to ESP32-S3 GPIOs.
- Use TFT_eSPI or LovyanGFX for fastest bring-up.
- Port only after Pico image/color baseline is stable.
