Runtime asset folder for Pico/SD streaming.

Primary target on device:
- /sd/assets

Source packs (PNG-heavy):
- assets/Enemies/
- assets/Characters/
- assets/UI/
- assets/Tilesets/
- assets/Icons/

Prepare Pico runtime assets from source packs:
- run: python prepare_pico_assets.py
- output: assets/runtime/
- format: 24-bit BMP only

Workspace mirror for preparation:
- assets/runtime/backgrounds/ (preferred)
- assets/runtime/recruits/ (preferred)
- assets/runtime/enemies/ (preferred)
- assets/runtime/icons/ (preferred)
- assets/backgrounds/
- assets/recruits/
- assets/sprites/recruits/ (supported)
- assets/Characters/ (supported alias)

Supported format:
- 24-bit BMP only

Scene backgrounds used by runtime (assets/backgrounds):
- save_slots.bmp
- guild_hall.bmp
- roster.bmp
- tavern.bmp
- recruit.bmp
- corrupted_tiles.bmp
- training.bmp
- settings.bmp
- log.bmp

Scene usage rules currently wired:
- missions -> corrupted_tiles.bmp (outside combat area)
- all non-mission scenes -> internal guild/building backgrounds

Background folder aliases currently supported:
- assets/runtime/backgrounds/
- assets/backgrounds/
- assets/Backgrounds/
- assets/sprites/backgrounds/

Recruit sprite overrides used by runtime:
1) <recruit_id>.bmp
2) char_<00..63>.bmp (deterministic unique pick by recruit id)
3) class_<job_class>.bmp
4) race_<race>.bmp
5) default.bmp

Recruit folder aliases currently supported:
- assets/runtime/recruits/
- assets/recruits/
- assets/sprites/recruits/
- assets/Characters/

Enemy sprite overrides used by runtime:
1) mission_<mission_slug>.bmp
2) difficulty_<1..5>.bmp
3) enemy_<difficulty>.bmp
4) enemy_<01..12>.bmp
5) default.bmp

Enemy folder aliases currently supported:
- assets/runtime/enemies/
- assets/Enemies/

UI icon overrides used by runtime:
- gold.bmp
- party.bmp
- mission.bmp
- a.bmp
- b.bmp
- default.bmp

Icon folder aliases currently supported:
- assets/runtime/icons/
- assets/Icons/

If no BMP exists, runtime falls back to procedural drawing in pico_sprites.py.
