# Next Steps - Completed Stages 1-5 (Thonny First)

This roadmap is now executed for stages 1-5 with a terminal-first workflow in Thonny. Web UI work is intentionally deferred until hardware screens arrive.

## Stage 1 - UI Theme Layer (Completed)

Status: done

Implemented:
- Shared theme helper in `ui_theme.py`.
- Shell renderer helpers (`header`, `section`, `panel`, `bullet`, `kv`).
- Optional OLED-compatible render mode via callback (`ui_theme.render(..., mode="oled")`).
- Kernels now render dashboards and sections using the shared theme.

Notes:
- Current default target is Thonny shell output.
- OLED callback path is available for later hardware integration.

## Stage 2 - Shared Micro-Kernel (Completed)

Status: done

Implemented:
- `kernel_core.py` with:
  - runtime directory initialization
  - common path map (`PATHS`)
  - boot diagnostics (data root, time source, memory, timestamp)
  - app registration and handoff API
- `main.py` now uses micro-kernel app registry and boot diagnostics.
- Shared path constants exposed in `game_paths.py`.

## Stage 3 - Sword World 2.5 Rules Expansion (Completed)

Status: done

Implemented:
- Terminology toggle (`official`/`fan`) in `sw25_kernel.py`.
- Fellow system with per-character toggle and d6 action table.
- Math engine module `sw25_math.py`:
  - success value check helper
  - K-table damage helper
- Low-memory campaign metadata streaming module `campaign_stream.py`.
- SW2.5 kernel now uses streamed campaign metadata loading + rule checks.

## Stage 4 - Guild Sim Progression Expansion (Completed)

Status: done

Implemented:
- Party roster virtualization module `roster_manager.py`:
  - recruits list
  - 1-4 active party IDs
  - active/inactive projection
- Category unlock rules in `guild_rules.py`:
  - gold + guild rank + roster XP gates
- Equipment/armor restriction matrix in `guild_rules.py`.
- Watch/attrition system in `watch_system.py`:
  - periodic fatigue and recovery ticks
  - mission attrition with injury timers
- `guild_sim_kernel.py` now includes:
  - recruit cycling in active party
  - category unlock flow
  - equipment assignment with blocked-skill behavior
  - mission attrition demo

## Stage 5 - Collection Book + Integrity (Completed)

Status: done

Implemented:
- `collection_book.py` with shared JSON ledger schema:
  - `monster_manual`
  - `item_ledger`
  - `hall_of_fame`
- `integrity.py` with SHA-256 manifest support:
  - manifest build
  - hash verify
  - JSON validation gate
- Manifest rebuild flows added to both kernels.
- Campaign loading path validates integrity/JSON before usage.
- Both kernels write collection events (monster/item/hall-of-fame entries).

## Current Operating Mode

- Primary target: Thonny shell monitor/input.
- Launcher: `main.py`.
- Apps:
  - `sw25_kernel.py`
  - `guild_sim_kernel.py`

## Deferred By Request

- No web UI work for now.
- Browser/Town-Dungeon asset port remains deferred until display hardware arrives.

## Suggested Immediate Test Pass (Thonny)

1. Run `main.py` and verify boot diagnostics prints.
2. Enter SW2.5 kernel and test:
   - terminology toggle
   - fellow action roll
   - campaign list/load
   - integrity manifest rebuild
3. Enter Guild Sim kernel and test:
   - category unlock attempts
   - recruit cycle
   - training + class unlock/purchase
   - weapon/armor restrictions on skill learning
   - mission attrition + hall of fame entry
4. Confirm files are written under data root:
   - `guild_sim/*.json`
   - `sw25/*.json`
   - `collections/collection.json`
   - `game_core/manifest.json`
