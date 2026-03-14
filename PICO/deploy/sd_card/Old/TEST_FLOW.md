# Thonny Manual Test Flow

This is a button-by-button smoke flow for your current Thonny-first build.

## Controls

- `w`: move up
- `s`: move down
- `enter`: select
- `q`: back/exit

## 1. Boot + Launcher

0. Optional clean slate first:
   - Run `reset_dev_data.py`

1. Open `main.py` in Thonny.
2. Run script.
3. Verify `BOOT DIAGNOSTICS` appears.
4. Confirm launcher shows:
   - `apps/ SW Digital`
   - `apps/Guild Sim`

## 1.1 Guild Sim Slot Flow

1. Enter `apps/Guild Sim`.
2. Confirm app menu shows:
   - `New Game`
   - `Continue`
   - `Quit`
3. Select `New Game` and pick a slot (`slot1`, `slot2`, or `slot3`).
4. Return to app menu and select `Continue` with the same slot.

## 2. SW2.5 Runner Flow

1. Enter `Sword World 2.5 Runner`.
2. Select `View Character Sheet`.
3. Verify fields show Name/Class/Level/Terminology/Fellow/Stats.
4. Select `Toggle Terminology (Official/Fan)`.
5. Select `Set Character Class` and verify prompt reflects current terminology.
6. Select `Toggle Fellow Mode` then `Run Fellow d6 Action`.
7. Select `Run 2d6 Check` once.
8. Select `Run K-table Damage Demo` once.
9. Select `List Campaign Files` and confirm campaign entries display.
10. Select `Create Campaign Template` and create one test campaign.
11. Select `List Campaign Files` again and confirm the new campaign appears.
10. Select `Load Campaign + Check` and run one campaign check.
11. Select `View Scenario Log Tail` and read last lines from the scenario log file.
11. Select `Add Hall Of Fame Entry`.
12. Select `Rebuild Integrity Manifest`.
13. Select `Save` then `Back to Launcher`.

Expected:
- No crashes.
- `Manifest entries: ...` is printed.
- Collection and character updates persist.

## 3. Guild Sim Flow (Inside Selected Slot)

1. Enter `Isekai Guild Simulator`.
2. Select `View Dashboard`.
3. Select `Rename Guild` and set your persistent guild and guild master names.
3. Select `List Roster`.
4. Select `Hire Recruit` and add at least one new recruit.
5. Select `Seed Recruit Pool` once.
5. Use `Assign Recruit To Party` and `Remove Recruit From Party` once each.
6. Select `Seed SW2.5 Campaign Templates` once.
7. Select `Cycle Active Recruit` at least once.
8. Select `Unlock Category (Guild Rules)` and try `Magic`.
5. Run `Train Melee (100g)` multiple times.
6. Run one of:
   - `Buy Warrior (2000g)`
   - `Buy Knight (5000g)`
7. Select `Equip Weapon/Armor` and test a restrictive loadout (`staff`, `heavy`).
8. Open `View Skill Catalog` and confirm blocked indicators show for restricted categories.
9. Try `Learn Skill` for a blocked high-tier magic skill to confirm restriction.
10. Run `Mission Attrition Demo` with difficulty `2` or `3`.
11. Run `Run Quest Simulation` and note the returned mission log file name.
12. Open `View Mission Log Tail` with that file name.
11. Select `Retire Recruit to Hall of Fame`.
12. Select `Rebuild Integrity Manifest`.
13. Select `Save` then `Back to Launcher`.

Expected:
- Gold/soul gems change after actions.
- Fatigue and injury timers update.
- Category unlock reason feedback prints.

## 4. File Output Checks

After both flows, confirm these files exist under data root (`sd` fallback on desktop):

- `sd/guild_sim/guild.json`
- `sd/guild_sim/roster.json`
- `sd/sw25/character.json`
- `sd/sw25/campaigns/starter_ruins.json`
- `sd/collections/collection.json`
- `sd/game_core/manifest.json`

## 5. Optional Automated Smoke

Run:

```powershell
C:/Users/RY0M/AppData/Local/Programs/Python/Python312/python.exe smoke_check.py
```

Expected final line:

`ALL SMOKE CHECKS PASSED`
