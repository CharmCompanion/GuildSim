# GuildSim Collaborator Handoff

## What This Project Is For
GuildSim is a retro guild-management game designed for Raspberry Pi Pico hardware with a 128x160 display.

The player manages a guild by recruiting units, training them, running missions, unlocking categories, and progressing guild rank.

## What It Does
- Runs a scene-based game loop on Pico hardware.
- Supports save slots and persistent progression.
- Uses seeded content for custom adventures and place/scene sharing.
- Includes a desktop editor for building scenes, seed packs, and content metadata.

## What It Needs
### Desktop (for coding/editor tooling)
- Python 3.11+
- Pillow
- VS Code + Copilot (optional but recommended)

### Pico Runtime (for device playtesting)
- Raspberry Pi Pico (or compatible)
- ST7735 1.8" display setup used by this repo
- Input wiring expected by the joystick/button module
- MicroPython modules available on device (for example machine)

## What It Has Right Now
- Pico runtime entrypoint via main.py and pico_app.py
- Core game systems in models.py
- Input adapter in pico_input.py
- Rendering helpers in pico_assets.py and pico_sprites.py
- Scene/content editor in ui_scene_builder.py
- Asset prep pipeline in prepare_pico_assets.py
- Saves in saves/slot1..slot3
- Scene/seed data under assets/layouts

## Core Files To Know First
- main.py: runtime launcher
- pico_app.py: main scene state machine + loop
- models.py: guild/recruit/mission/progression logic
- ui_scene_builder.py: desktop scene and seed editor
- prepare_pico_assets.py: desktop asset conversion/prep

## Easy Game Loop Summary
This is the runtime loop in plain terms:

1. Boot runtime, initialize display/input, set starting scene.
2. Ensure save folders exist.
3. Repeat forever:
4. Tick game time updates (fatigue/injury/recovery/progression timing).
5. Poll input from stick/buttons.
6. Route input to current scene handler.
7. Render current scene.
8. Sleep briefly, then continue.

Scene flow highlights:
- save_slots: pick/load/delete save slot
- dashboard: hub to roster/tavern/missions/training/settings/seeds/log
- roster: view recruits and party status
- tavern: recruit generation/selection
- recruit: recruit detail tabs (stats/train/class/skills/party)
- missions: choose and resolve missions
- training: unlock categories and apply training
- settings: rename/cycle options, add example seeds, return to save slots
- seeds: browse preloaded seed library entries
- log: recent mission results

## Easy Editor Summary
ui_scene_builder.py is the desktop authoring tool.

Main editor capabilities:
1. Scene editing canvas with top/perspective views.
2. Sprite sheet picker with cell selection and drag selection.
3. Paint/select/shape/text/marker tools.
4. Transform tools (rotate/flip/scale/pivot).
5. Layer system with base/new/duplicate/remove + hide/lock + assign selected.
6. Adventure seed builder and loader.
7. Place/scene seed generation and seed pack import/export.
8. Seed library with metadata (author/description/rating/timestamps).
9. Dependency check/remap for missing asset paths in place seeds.
10. Import/export workflow for local sharing.

## Typical Collaborator Workflow
1. Pull latest main.
2. Run/modify desktop editor features first (ui_scene_builder.py).
3. Test seed/library JSON behavior under assets/layouts.
4. If changing runtime logic, update pico_app.py and models.py together.
5. Validate with quick compile checks on desktop.
6. If hardware testing is needed, deploy to Pico and test controls/scenes.

## Important Notes For VS Code + Copilot
- Runtime file pico_app.py imports MicroPython-specific modules, so full desktop execution of runtime will fail without hardware-compatible environment.
- Desktop-side work is best done in ui_scene_builder.py and prepare_pico_assets.py.
- Keep seed formats stable (ADV- and PLC- prefixes) so runtime/editor stay compatible.

## Quick Start Commands (Desktop)
- Compile check editor:
  python -m py_compile ui_scene_builder.py
- Launch editor:
  python ui_scene_builder.py

## Collaboration Goal
Use this repo as a single source for:
- Game runtime behavior (Pico)
- Content authoring pipeline (desktop)
- Seed-based sharing and reproducible content
