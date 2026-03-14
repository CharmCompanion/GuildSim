# Pico Native Build (128x160 ST7735)

This project has been converted from Flask/web UI into a Pico-native scene app.

## Runtime Files

- `main.py`: launches Pico app
- `guild_sim_main.py`: compatibility launcher (also launches Pico app)
- `pico_app.py`: scene controller + game flow
- `pico_input.py`: ADS7830 joystick + A/B input
- `pico_sprites.py`: deterministic mini-sprite renderer
- `models.py`: full game mechanics and save system

## Required Pico Modules

Put these on the Pico filesystem:

- `main.py`
- `guild_sim_main.py`
- `pico_app.py`
- `pico_input.py`
- `pico_sprites.py`
- `models.py`
- `lcd.py` (your ST7735 driver with `LCD_1inch8`)

## Wiring

- ADS7830 SDA/SCL -> GP4/GP5
- Joystick X -> ADS7830 A0
- Joystick Y -> ADS7830 A1
- Joystick click -> GP14
- Button A (Select) -> GP15 to GND
- Button B (Back) -> GP16 to GND
- LCD BL expected on GP13 (PWM)

## Scene Controls

- Stick up/down: move selection
- Stick left/right: switch tabs (recruit detail)
- A: select / confirm action
- B: back scene
- Stick click: quick-train in Training scene
- In Recruit scene: hold B and press stick click to release recruit

## Feature Coverage

All previous web gameplay features are retained:

- Save slots (create/load/delete)
- Guild dashboard and rank progression
- Roster and recruit detail
- Tavern hiring + refresh
- Missions + refresh + mission log
- Training category unlocks
- Recruit training, class promotion, skill learning
- Party management (max 4, cannot remove last active)
- Tick-based recovery/fatigue updates
- Guild/Lord rename (preset cycling on device)

## Notes

- This is now a Pico-first codebase; Flask routes/templates are removed.
- Sprite rendering is procedural for speed and memory safety.
- If you later want bitmap sprite sheets, add a tile/sprite blitter and map layers in `pico_sprites.py`.
