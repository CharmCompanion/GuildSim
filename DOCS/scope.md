# Guildmaster V-Pet Scope

## Goal
Build a playable device-first virtual pet RPG loop with progression from 1 adventurer to a full party of 4, including training, quests, gear, and lightweight tactical combat.

## Platform Decision (Updated)
- Primary recommendation: ESP32-S3 (N16R8) using C/C++ (ESP-IDF or Arduino Core), not MicroPython for final product.
- Why:
  - Need to support up to 4 party members + up to 3 enemies + animated combat.
  - Need stable memory use, predictable frame times, and lower runtime overhead.
  - MicroPython remains useful for quick prototyping only.

## Core Product Pillars
- Virtual pet care and growth loop.
- Party progression loop (unlock 2nd, 3rd, 4th members over rank).
- Combat loop with animated units, skills, and enemies.
- Long-term progression via quests, tower floors, gear, and class identity.

## Progression Gates
- Rank 0-1:
  - Start with 1 recruit.
  - Unlock: care (feed/rest), basic training, 3 quest choices.
- Rank 2:
  - Unlock 2nd adventurer slot.
  - Unlock recruit menu (choose 1 of 4 generated recruits).
  - Unlock basic shop and equipment.
- Rank 3:
  - Unlock 3rd adventurer slot.
  - Unlock class-focused training paths.
- Rank 4:
  - Unlock 4th adventurer slot.
  - Unlock advanced quests and tower access.

## Systems In Scope

### 1) Adventurer Lifecycle
- Needs: hunger, mood, energy, training focus.
- Stats: STR, AGI, VIT, INT, SPR.
- Progression: XP, level, rank contribution.
- Identity: generated name, portrait/sprite variant, starting trait.

### 2) Recruit System
- Show 4 candidates at recruit unlock points.
- Candidate card includes:
  - name
  - base stats
  - starting skill affinity
  - current gear
  - passive trait
- Player hires one candidate and can reroll for a cost.

### 3) Class-by-Gear Model
- Base class starts as Recruit.
- Effective class determined by equipped weapon/armor profile.
- Four class archetypes:
  - Knight/Tank (melee)
  - Mage
  - Scout
  - Priest/Healer/Enchanter
- Skills unlocked by class profile + training path.

### 4) Training System
- Training options:
  - Melee room
  - Magic room
  - Ranged room
- Implementation option A (faster): one school room, swap FG overlay by training type.
- Output: stat growth, skill XP, fatigue/energy cost.

### 5) Quest System (3 Choices)
- Every cycle offers 3 quest cards:
  - Safe
  - Balanced
  - Risky
- Rewards: XP + loot + gold.
- Risk and success influenced by:
  - party stats
  - current needs penalties
  - class/skill tags

### 6) Combat System (New Scope)
- Encounters support:
  - Party: 1 to 4 units
  - Enemies: 1 to 3 units
- Enemy tiers:
  - normal
  - elite
  - boss
- Combat style target:
  - lightweight turn timeline (AGI-based order)
  - basic skill cooldowns
  - status effects (small set)
- Animation requirement:
  - animated sprites for adventurers and enemies
  - simple telegraph/impact effects

### 7) Tower/Floor Progression (Preferred over dungeon)
- Floor-based challenge ladder.
- Each floor has encounter seed + reward table.
- Boss floors every N levels (example: every 5 floors).
- Meta progression:
  - unlocks shop tiers
  - unlocks training efficiency
  - unlocks recruit quality

### 8) Scenes and Layering
- Required scenes:
  - Guild main scene (home)
  - Adventurer room(s) (one per unlocked unit)
  - Shop scene
  - School scene
  - Combat scene
  - Recruit menu scene
  - Tower menu scene
- Layer order policy in world scenes:
  - BG -> actor layer -> FG overlay -> UI
- FG masking required so actors can pass behind foreground props.

### 9) Inventory and Equipment
- Inventory supports consumables and equipment.
- Equipment slots:
  - weapon
  - armor
  - accessory
- Shop supports:
  - buy
  - equip
  - hold in inventory
  - optional sell

## AI and Enemy Behavior (Simple First)
- Enemy action weights by role:
  - striker
  - tank
  - support
- Boss pattern table:
  - phase 1 move list
  - phase 2 trigger at HP threshold
  - signature skill cooldown

## Performance Targets
- Target frame rate: 30 FPS world, 30-60 FPS combat effects depending on load.
- Memory policy:
  - texture atlas usage
  - pool projectile/effect objects
  - avoid per-frame allocations in combat loop
- Unit budget in active combat:
  - up to 4 ally animators
  - up to 3 enemy animators
  - plus UI and effect layers

## Vertical Build Order (Practical)
1. Core data model + save/load.
2. Single adventurer care loop (feed/rest/train).
3. 3-choice quest loop with rewards.
4. Recruit menu (4 candidates) and 2nd slot unlock.
5. Combat prototype (1v1 -> 2v2 -> 4v3).
6. Class-by-gear + skills.
7. Tower floors + boss encounters.
8. Scene polish, FG layering, room/shop/school UX.

## Checklist
- [ ] One-adventurer playable loop stable.
- [ ] Rank gate unlocks 2nd, 3rd, 4th adventurer.
- [ ] Recruit menu shows 4 generated candidates with names.
- [ ] Class determined by gear profile.
- [ ] 3 quest cards with risk/reward variation.
- [ ] Combat supports up to 4 allies vs 3 enemies.
- [ ] Enemy sprites animated.
- [ ] Boss encounter logic implemented.
- [ ] Tower floor progression implemented.
- [ ] Guild/rooms/shop/school scenes with BG/FG layering.
- [ ] Performance acceptable on chosen hardware.
- [ ] Save/load robust for long-term play.

## Deferred (Not in immediate scope)
- Emulator launcher mode.
- Online features.
- Advanced crafting/economy.
- Procedural open dungeon generation.

## Engine Architecture (Production, ESP32-S3 C/C++)

### Runtime Stack
- Language: C++17.
- Runtime target: ESP32-S3 N16R8.
- Framework path:
  - Phase 1: Arduino Core for ESP32 (fast bring-up).
  - Phase 2: ESP-IDF componentized build (production hardening).
- Graphics approach:
  - SPI TFT driver with sprite batching and dirty rectangles where possible.
  - 16-bit RGB565 assets.
- Storage:
  - Flash partitions for firmware and static assets.
  - Optional SD for large art/audio expansions.

### Top-Level Modules
- `app_main`
  - Boot sequence, hardware init, scene bootstrap.
- `platform`
  - Display, input, audio, timers, filesystem abstraction.
- `engine`
  - Scene manager, update loop, render dispatcher.
- `ui`
  - Menus, widgets, focus/navigation, bars/cards.
- `game_state`
  - Guild, adventurers, quests, inventory, progression flags.
- `systems`
  - Needs, training, rewards, shop, recruitment, class resolver.
- `combat`
  - Turn timeline, skills, AI, status effects, encounter resolution.
- `content`
  - Data tables for items, skills, enemies, floors, quests.
- `save`
  - Serialization, migration versioning, slot management.

### Scene State Machine
- `SCENE_BOOT`
- `SCENE_GUILD_HOME`
- `SCENE_RECRUIT_MENU`
- `SCENE_ADVENTURER_ROOM`
- `SCENE_SCHOOL`
- `SCENE_SHOP`
- `SCENE_QUEST_PICK`
- `SCENE_COMBAT`
- `SCENE_RESULTS`
- `SCENE_TOWER_MAP`

Rules:
- Scene transitions must be explicit and single-step.
- No scene directly edits unrelated scene state; all shared data flows through `game_state`.

### Main Loop Budget
- Target frame: 33 ms (30 FPS).
- Loop phases:
  - Input sample: <= 2 ms
  - Simulation update: <= 8 ms
  - Render submission: <= 18 ms
  - Audio/UI overhead: <= 5 ms
- If frame budget exceeded:
  - drop optional particle effects first
  - reduce animation frame advance frequency
  - keep simulation deterministic

### Rendering Model
- Layer order:
  - BG tile/scene
  - actor sprite layer
  - FG mask/overlay
  - UI/HUD
- Sprite system:
  - atlas-backed frame lookup
  - per-entity animation controller
  - no dynamic allocations during draw
- Combat entity limits:
  - allies: max 4
  - enemies: max 3
  - bosses count as one entity with larger sprite/effect budget

### Memory Budget (Starting Targets)
- Internal RAM:
  - frame buffers and hot runtime state
- PSRAM:
  - sprite atlases, combat assets, scene overlays
- Budget targets:
  - Display/backbuffer + working surfaces: <= 220 KB
  - Runtime game state: <= 128 KB
  - UI/widget state: <= 64 KB
  - Combat transient state/effects: <= 192 KB
  - Asset caches in PSRAM: dynamic, capped by policy

Allocation policy:
- Pre-allocate fixed pools for entities, projectiles, effects, and UI cards.
- Avoid heap churn inside update/render loops.
- Use ring buffers for logs and combat events.

### Data Architecture
- Authoring format:
  - JSON or CSV at build time.
- Runtime format:
  - packed binary tables for fast lookup.
- Required tables:
  - items
  - skills
  - enemies
  - floor definitions
  - quest templates
  - recruit name fragments/traits

### Save System
- Save slots: 3.
- Save blob includes:
  - guild progression
  - adventurer roster
  - inventory and equipment
  - tower floor progress
  - active timers/needs state
- Save safety:
  - temp-write then atomic replace
  - checksum + version field

### Combat Architecture
- Turn engine:
  - AGI-based timeline queue.
- Action model:
  - basic attack, skill use, item use, guard.
- Skill model:
  - cost, cooldown, tags, target rules.
- Status model:
  - compact bitset + duration counters.
- Enemy AI:
  - weighted action selector + phase table for bosses.

### Input Architecture (Including Thumbstick)
- Input abstraction:
  - digital buttons: confirm/cancel/menu.
  - analog stick: menu axis + movement axis.
- Thumbstick handling:
  - calibrate center at boot
  - configurable deadzone
  - repeat delay for menu navigation

### Content Pipeline
- PC-side build tools convert source PNG sheets to:
  - atlas textures
  - frame metadata (rect, pivot, duration)
  - optional collision/anchor points
- Enemy and adventurer animations share same metadata format.

### Milestones (Engineering)
1. Platform bring-up:
  - display + input + save write/read smoke tests.
2. Core runtime:
  - scene manager + game_state + stable loop.
3. World layer:
  - guild scene with BG/actor/FG correctness.
4. Systems layer:
  - needs, training, recruit, shop, quests.
5. Combat layer:
  - 4v3 functional with enemy animations and boss behavior.
6. Performance pass:
  - pool tuning, frame pacing, memory telemetry.
7. Playability pass:
  - balancing and retention loop polish.

### Definition Of Done (Device Playable)
- Can start new game and play a full loop without crashes.
- Unlock path from 1 to 4 adventurers works.
- Recruit menu with 4 generated candidates works.
- Shop/equipment/class access works.
- Quest flow and 3-choice selection works.
- Tower floors and boss encounters work.
- Combat supports up to 4 allies vs 3 enemies at stable frame time.
- Save/load survives reboot and version check.
