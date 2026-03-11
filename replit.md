# Guild Device - Pico Native Runtime

## Current Status

This workspace is now Pico-native and no longer runs the Flask web stack.

Primary runtime entrypoints:
- `main.py`
- `guild_sim_main.py`

Primary runtime modules:
- `pico_app.py` (scene/state machine)
- `pico_input.py` (ADS7830 joystick + A/B buttons)
- `pico_sprites.py` (lightweight recruit sprite drawing)
- `models.py` (core gameplay systems + save/load)
- `lcd.py` (adapter import for `LCD_1inch8`)
- `st7735_1inch8.py` (LCD driver)

## Input Mapping

- Joystick X/Y via ADS7830 A0/A1 over I2C (GP4/GP5)
- Stick click: GP14
- A (Select): GP15
- B (Back): GP16

## Scene Controls

- Stick up/down: list navigation
- Stick left/right: recruit tab switch
- A: select/confirm action
- B: back
- Stick click: quick train in Training scene

## Save Data

- `saves/slot1`, `saves/slot2`, `saves/slot3`

## Deployment Split

Use `PICO_PORTING.md` and `DEPLOY_SPLIT.md` to keep:
- only runtime files on Pico internal flash
- heavy assets/tools/archives on SD card
