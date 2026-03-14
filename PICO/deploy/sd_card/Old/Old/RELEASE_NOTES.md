# Release Notes

## v1.0.0-final-thonny (2026-03-09)

Finalized terminal-first dual-project build for Raspberry Pi Pico W + SD workflow.

### Added
- Unified launcher and micro-kernel diagnostics (`main.py`, `kernel_core.py`).
- Guild identity persistence and display in launcher.
- Full Guild Sim admin loop (`guild_sim_kernel.py`):
  - roster hire/release
  - active party assignment/removal (1-4)
  - training and class progression
  - category unlock economy gates
  - weapon/armor restrictions and skill blocking
  - archive unlock and skill learning
  - quest simulation rewards/failures
  - mission attrition, injury, fatigue updates
- Full SW2.5 text runner (`sw25_kernel.py`):
  - terminology toggle
  - Fellow mode + d6 action table
  - 2d6 success checks
  - K-table damage helper usage
  - campaign template creation and loading
- Shared collection book and integrity systems:
  - `collection_book.py`
  - `integrity.py`
- Shared mission logging (`mission_log.py`) and log tail readers.
- Seed utility without town generation (`seed_world.py`).
- Reset utility (`reset_dev_data.py`).

### Data/Storage
- SD-first storage with desktop fallback.
- Structured save paths for guild, roster, character, campaigns, collections, and manifest.

### Documentation
- `NEXT_STEPS.md` completed for stages 1-5.
- `TEST_FLOW.md` manual validation runbook.
- `DEPLOY_TO_PICO.md` hardware deployment checklist.
- `DEPLOY_TO_PI_ZERO.md` VS Code-only Raspberry Pi Zero deployment workflow.
- `OPEN_VPET_FORK_PLAN.md` migration blueprint for forking Open VPet into open-guild-sim.
- `FINAL_VERSION.md` final scope status.

### Validation
- Automated regression smoke check passes:
  - `ALL SMOKE CHECKS PASSED`
- Diagnostics report no errors in core final files.

### Deferred By Design
- Web UI implementation is intentionally deferred.
- Primary runtime target remains Thonny shell until display hardware arrives.
