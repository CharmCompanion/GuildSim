# Final Version Status (Thonny/Pico Build)

Date: 2026-03-09

This workspace is now in a release-ready state for terminal-first play/testing in Thonny and deployment to Pico W with SD storage.

## Included Projects

1. Sword World 2.5 Runner (`sw25_kernel.py`)
- Character profile and persistent saves
- Terminology toggle (official/fan)
- Fellow mode with d6 action table
- 2d6 check engine and K-table damage helper
- Campaign template creation
- Streamed campaign metadata reading
- Integrity and JSON validation gates
- Scenario logging and log tail viewer
- Hall of fame and collection hooks

2. Isekai Guild Simulator (`guild_sim_kernel.py`)
- Persistent guild identity (name + guild master)
- Roster management: hire/release recruits
- Active party assignment/removal (1-4)
- Category unlock economy (gold/rank/roster XP)
- Training and class unlock/purchase loop
- Skill archive unlock and affinity discount logic
- Weapon/armor restrictions affecting skill usability
- Mission attrition, fatigue, and injury timers
- Quest simulation with rewards/failures
- Mission logging and log tail viewer
- Collection and hall of fame hooks

## Shared Platform Components

- `main.py`: bootstrap launcher
- `kernel_core.py`: runtime dirs, diagnostics, app handoff
- `storage.py` + `sd_setup.py`: SD mount or desktop fallback
- `integrity.py`: SHA-256 manifest creation/verification
- `collection_book.py`: shared monster/item/hall-of-fame ledger
- `ui_theme.py`: unified shell-first renderer (OLED callback-ready)
- `mission_log.py`: line-by-line text logs for low memory
- `seed_world.py`: guild rename + recruit/campaign seeding (no town generation)
- `reset_dev_data.py`: clean reset of save data
- `smoke_check.py`: non-interactive regression checks
- `TEST_FLOW.md`: full manual validation script

## Recommended Run Order

1. Optional reset: run `reset_dev_data.py`
2. Start launcher: run `main.py`
3. Validate both kernels via `TEST_FLOW.md`
4. Regression check: run `smoke_check.py`

## Known Constraints

- Primary runtime target is Thonny shell until OLED/buttons are connected.
- Web UI is intentionally deferred by request.
- NTP sync is opportunistic; local RTC fallback is automatic.
