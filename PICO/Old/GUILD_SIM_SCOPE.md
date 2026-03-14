# Guild Sim Scope (Current As-Built)

## 1) Product Shape Right Now
Guild Sim is currently a menu-driven, save-backed, single-session management RPG kernel focused on:
- Guild resources (gold, soul gems, rank)
- Recruit roster and active party management (up to 4 active)
- Training and class progression
- Skill unlock/learn economy
- Simple quest simulation and attrition
- Lightweight persistence/integrity/logging support

Primary runtime entry:
- `guild_sim_main.py`
- `main.py` app picker integration (slot-aware New Game / Continue)

Primary gameplay kernel:
- `guild_sim_kernel.py`

Deploy mirror exists for Pico app packaging:
- `Deploy/apps/guild_sim/guild_sim_kernel.py`
- `Deploy/apps/guild_sim/main.py`

## 2) Core Data Model
### Guild State
Stored in `guild.json` (or slot path variant):
- `guild_name`
- `lord`
- `rank`
- `gold`
- `soul_gems`
- `unlocked_categories` (starts with `Melee`)

Defaults in `guild_sim_kernel.py` (`DEFAULT_GUILD`).

### Roster State
Stored in `roster.json` (or slot path variant):
- `recruits[]` with per-recruit fields:
  - id, name, class, affinity, xp
  - stats: STR/DEX/AGI/INT/VIT/SPR
  - training_lvls: Melee/Magic/Range/Passive
  - eligible_to_buy
  - learned_skills
  - archive_unlocked
  - weapon_type, armor_weight
  - injury_until, equipment_fatigue
- `active_party_ids[]` (1-4)

Defaults and helpers in `roster_manager.py`.

### Save Slot Structure
3 slots supported:
- `guild_sim/slots/slot1/`
- `guild_sim/slots/slot2/`
- `guild_sim/slots/slot3/`

Per-slot files:
- `guild.json`
- `roster.json`

Implemented in `guild_sim_kernel.py` via `SLOT_IDS`, `_slot_paths`, `list_slot_status`, `init_new_game_slot`.

## 3) Systems Implemented
### A) Guild/Meta
- Rename guild + guild master (`rename_guild_flow`)
- Save all (`save_all`)
- Dashboard view (`view_dashboard`)
- Slot-aware New/Continue via launcher menu in `main.py`

### B) Recruitment + Party Ops
- Hire recruit (manual name + optional affinity)
- Seed random recruit pool (bulk)
- Assign/remove active party members
- Release recruit from roster
- Cycle selected active recruit
- Hard guard against removing last active recruit

Main code:
- `guild_sim_kernel.py`
- `roster_manager.py`
- `seed_world.py`

### C) Training + Class Progression
Training categories:
- Melee, Magic, Range, Passive

Effects per train action:
- Costs gold (100)
- Increases category training level
- Adds XP (+10)
- Boosts category-linked stats (`CATEGORY_MAP`)
- Triggers class eligibility checks (`_unlock_by_training`)

Class purchase system:
- Warrior, Knight, Mage, Ranger
- Requires eligibility + gold cost
- Changes recruit class on buy
- Records class license item in collection book

Main code:
- `guild_sim_kernel.py`

### D) Category Unlock Rules (Guild-Level Gates)
Unlockable guild categories:
- Magic, Range, Passive

Gate dimensions:
- Guild gold threshold
- Guild rank threshold
- Total roster XP threshold

Rule table:
- `guild_rules.py` (`CATEGORY_UNLOCK_RULES`)

Flow:
- `unlock_category_flow` -> `try_unlock_category`

### E) Equipment Restriction Layer
Recruit loadout:
- weapon_type: sword/staff/bow
- armor_weight: light/medium/heavy

Rule behavior:
- Certain combinations block high-tier skills in categories (A/B/S gate behavior)
- `blocked_skill_categories` + `_blocked_by_gear`

Main code:
- `guild_rules.py`
- `guild_sim_kernel.py`

### F) Skill Economy + Archive
Catalog:
- Unified static skill list in `skills_catalog.py`
- Categories include Combat, Magic, Utility, Passive
- Rank tiering D/C/B/A/S
- Some skills are lock-tagged (`locked=True`)

Skill interactions:
- View catalog with lock/block status
- Unlock locked archive skills with soul gems (`cost * 2`)
- Learn unlocked skills with soul gems
- Affinity discount (30%) when recruit affinity matches skill category
- Learned skill list view

Main code:
- `skills_catalog.py`
- `guild_sim_kernel.py`

### G) Quest + Attrition Simulation
Mission attrition demo:
- Applies fatigue/injury pressure by difficulty

Quest simulation loop:
- Difficulty input (1-5)
- Party power calculation from stats
- Injury reduces contribution
- Encounter roll comparison for success/failure
- Success rewards gold/soul gems/xp + collection entries
- Failure applies recovery cost
- Writes mission logs line-by-line

Main code:
- `guild_sim_kernel.py`
- `watch_system.py`
- `mission_log.py`
- `collection_book.py`

### H) Real-Time Watch Tick
While kernel loop runs:
- Every ~10s, active recruits tick
- Passive VIT recovery
- Equipment fatigue increments
- Injury timers resolve when elapsed

Main code:
- `guild_sim_kernel.py` main loop
- `watch_system.py`

### I) Logs, Collection, Integrity
- Mission logs append/tail (`mission_log.py`)
- Hall-of-fame retire action (`record_hof`)
- Item/monster collection recording from class buys/quests
- Integrity manifest rebuild action (`build_manifest`)

Main code:
- `mission_log.py`
- `collection_book.py`
- `integrity.py`
- `guild_sim_kernel.py`

### J) Seed Content Utilities
- Random recruit name generation
- Recruit pool seeding
- SW2.5 campaign template file generation

Main code:
- `seed_world.py`

## 4) Player-Facing Menu Surface (Current)
From `guild_sim_kernel.py`, title `ISEKAI GUILD SIM`:
- View Dashboard
- Rename Guild
- List Roster
- Hire Recruit
- Seed Recruit Pool
- Assign Recruit To Party
- Remove Recruit From Party
- Release Recruit
- Cycle Active Recruit
- Seed SW2.5 Campaign Templates
- Unlock Category (Guild Rules)
- Train Melee / Magic / Range / Passive
- Buy Warrior / Knight / Mage / Ranger
- Equip Weapon/Armor
- View Skill Catalog
- Unlock Archive Skill
- Learn Skill
- Show Learned Skills
- Check Stats
- Mission Attrition Demo
- Run Quest Simulation
- View Mission Log Tail
- Retire Recruit to Hall of Fame
- Rebuild Integrity Manifest
- Save
- Back to Launcher

## 5) Scope Boundaries / Current Gaps
Implemented but intentionally lightweight:
- No town-building simulation loop (economy layers/building chains not yet deep)
- No authored narrative campaign state machine; quests are simulated encounters
- No enemy roster/AI combat rounds; power-vs-roll abstraction only
- No itemized inventory/equipment stats beyond weapon/armor gate behavior
- No recruitment costs/upkeep economy tuning beyond simple gold spend actions
- No relationship/morale/faction sub-systems yet
- No full LCD-native compact UI parity with all kernel actions in one polished UX shell yet

## 6) Expansion-Ready Backlog (Practical Next Steps)
### Phase 1: Core Gameplay Depth
- Add structured expedition model: mission type, biome, hazards, rewards, retreat
- Add recruit condition model: HP/stress/morale/trauma instead of only fatigue+injury
- Add enemy archetype tables and deterministic combat resolution layers

### Phase 2: Economy + Town Layer
- Add buildings (forge/library/inn/chapel) with upgrade trees and passive effects
- Add weekly payroll/supplies/upkeep sinks to stabilize economy pacing
- Add market/events/contract board for decision pressure

### Phase 3: Character Identity
- Add traits/background/perks for recruit differentiation
- Add class advancement trees and specialization branches
- Add equipment inventory with stat modifiers and durability

### Phase 4: Long-Run Meta
- Add season/year calendar and world-state events
- Add story arcs/factions/reputation meters
- Add victory/failure conditions and legacy carryover between slots

### Phase 5: UX/Platform
- Build compact LCD-first page architecture mapping kernel actions to 160x128 constraints
- Add save indicators/error states and deterministic input debouncing
- Add optional desktop debug shell that shares same game state schema

## 7) Important File Map
- Runtime kernel: `guild_sim_kernel.py`
- App entry: `guild_sim_main.py`
- Launcher integration: `main.py`
- Rules: `guild_rules.py`
- Roster domain: `roster_manager.py`
- Skill catalog: `skills_catalog.py`
- Watch/attrition: `watch_system.py`
- Mission logs: `mission_log.py`
- Seed tools: `seed_world.py`
- Save paths: `game_paths.py`, `storage.py`, `kernel_core.py`
- Deploy mirror: `Deploy/apps/guild_sim/*`

## 8) Notes for Refactor Safety
- Keep `guild_sim_kernel.py` and `Deploy/apps/guild_sim/guild_sim_kernel.py` in sync.
- Preserve recruit field normalization behavior for backward-compatible saves.
- Preserve slot path layout to avoid save migration breakage.
- Keep menu labels stable if external scripts rely on action ordering.
