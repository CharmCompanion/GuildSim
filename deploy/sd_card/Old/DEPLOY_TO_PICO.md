# Deploy To Pico W (Final Build)

This guide deploys the final Thonny-first build to Raspberry Pi Pico W + SD module.

## 1. Hardware Wiring (SPI0)

- Pico `3V3 (Pin 36)` -> SD `VCC`
- Pico `GND (Pin 38)` -> SD `GND`
- Pico `GP16 (Pin 21)` -> SD `MISO/DO`
- Pico `GP17 (Pin 22)` -> SD `CS`
- Pico `GP18 (Pin 24)` -> SD `SCK/CLK`
- Pico `GP19 (Pin 25)` -> SD `MOSI/DI`

## 2. Preferred 3-Folder Deploy Layout

Use the prepared structure under `Deploy/`:

- `Deploy/Core/`
- `Deploy/apps/guild_sim/`
- `Deploy/apps/sw_digital/`
- `Deploy/apps/open_vpet/`

Upload to Pico as:

- `/Core/*` from `Deploy/Core/`
- `/apps/guild_sim/*` from `Deploy/apps/guild_sim/`
- `/apps/sw_digital/*` from `Deploy/apps/sw_digital/`
- `/apps/open_vpet/*` from `Deploy/apps/open_vpet/`

Run one game directly:

- `/apps/guild_sim/main.py`
- `/apps/sw_digital/main.py`
- `/apps/open_vpet/main.py`

Each app main adds `/Core` to `sys.path` so the app can run standalone with Core.

If you want to refresh Deploy files from current source before copying, run:

```powershell
./build_deploy_tree.ps1
```

For a fresh overwrite deploy from terminal (remove existing app/core folders first):

```powershell
./deploy_to_pico.ps1 -Port COM3 -App all -Clean
```

## 2.1 Optional Root Launcher Deploy

If you also want the root launcher (`main.py`) flow, copy these to Pico root too:

- `main.py`
- `reset_dev_data.py`

## 3. SD Card Folder Layout

These folders/files are auto-created at first boot if missing, but you can pre-create them:

- `/sd/game_core/`
- `/sd/game_core/manifest.json`
- `/sd/collections/`
- `/sd/collections/collection.json`
- `/sd/sw25/`
- `/sd/sw25/character.json`
- `/sd/sw25/campaigns/`
- `/sd/sw25/campaigns/starter_ruins.json`
- `/sd/guild_sim/`
- `/sd/guild_sim/guild.json`
- `/sd/guild_sim/roster.json`
- `/sd/guild_sim/logs/`

## 4. First Boot Sequence

1. In Thonny, connect to Pico interpreter.
2. Optional: set hardware profile before first game run:

```python
import sys
sys.path.append('/Core')
from hardware_runtime import set_profile
set_profile('pico_w_lcd_1_8')  # or 'pico_w_terminal', 'esp32_c6_touch', etc.
```

3. Run `reset_dev_data.py` once.
4. Run `main.py`.
5. Confirm `BOOT DIAGNOSTICS` prints:
  - data root
  - active hardware profile
  - display/storage capability lines
  - time source
  - memory
6. Enter `Isekai Guild Simulator` and run:
   - `Rename Guild`
   - `Seed Recruit Pool`
   - `Save`
7. Enter `Sword World 2.5 Runner` and run:
   - `Create Campaign Template`
   - `Save`

## 5. Runtime Controls (Both Kernels)

- `w` = up
- `s` = down
- `enter` = select
- `q` = back/exit

## 6. Integrity + Save Verification

After first session, verify these options run without errors:

- In Guild Sim: `Rebuild Integrity Manifest`
- In SW2.5: `Rebuild Integrity Manifest`

Then inspect SD files in Thonny Files pane:

- `/sd/game_core/manifest.json`
- `/sd/collections/collection.json`
- `/sd/guild_sim/guild.json`
- `/sd/guild_sim/roster.json`
- `/sd/sw25/character.json`

## 7. Troubleshooting

- If SD is not found:
  - Recheck wiring and SPI pin mapping.
  - Re-seat SD card.
  - Reboot Pico and run `main.py` again.
- If imports fail:
  - Ensure all files listed in section 2 are copied.
- If menu appears but actions fail:
  - Run `reset_dev_data.py` and retry.

## 8. Optional Desktop Regression

Before flashing changes, run on desktop:

```powershell
C:/Users/RY0M/AppData/Local/Programs/Python/Python312/python.exe smoke_check.py
```

Expected final line:

`ALL SMOKE CHECKS PASSED`
