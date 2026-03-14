# ESP32-S3 Engine Bootstrap

This document is the immediate build guide for migrating Guildmaster V-Pet from MicroPython prototype to a production C/C++ runtime on ESP32-S3 DevKitC-1 N16R8.

## 1) Wiring Plan (ST7735 1.8in SPI)

Use 3.3V logic only.

Suggested pin map (safe defaults, remappable in code):

- TFT VCC -> 3V3
- TFT GND -> GND
- TFT SCL/CLK -> GPIO12
- TFT SDA/MOSI -> GPIO11
- TFT CS -> GPIO10
- TFT DC -> GPIO9
- TFT RST -> GPIO14
- TFT BL -> GPIO13 (PWM capable)

Optional input wiring:

- BTN A -> GPIO4 (to GND when pressed, use INPUT_PULLUP)
- BTN B -> GPIO5
- BTN MENU -> GPIO6

PSP thumbstick module (example):

- VRx -> GPIO1 (ADC)
- VRy -> GPIO2 (ADC)
- SW  -> GPIO3 (digital input pullup)
- VCC -> 3V3
- GND -> GND

Notes:

- Keep SPI wires short while bringing up display.
- If display is black, test BL pin first by forcing high duty PWM.
- If colors are wrong, check RGB/BGR and byte-order in driver.

## 2) Recommended Software Path

- Phase 1: Arduino Core for ESP32 (fast bring-up and easier iteration).
- Phase 2: ESP-IDF (if needed for deeper memory control and production hardening).

## 3) Project Skeleton (C/C++)

Create this structure in your new ESP firmware workspace:

- src/main.cpp
- src/platform/display.hpp
- src/platform/display_st7735.cpp
- src/platform/input.hpp
- src/platform/input_buttons_stick.cpp
- src/engine/scene_manager.hpp
- src/engine/scene_manager.cpp
- src/game/game_state.hpp
- src/game/game_state.cpp
- src/scenes/scene_guild_home.cpp
- src/scenes/scene_recruit_menu.cpp
- src/scenes/scene_quest_pick.cpp
- src/scenes/scene_combat.cpp
- src/systems/needs_system.cpp
- src/systems/quest_system.cpp
- src/systems/combat_system.cpp
- src/data/static_tables.hpp
- src/save/save_slot.cpp

## 4) Bring-Up Checklist (First Boot)

1. Confirm board flash/PSRAM are detected at startup logs.
2. Run solid-color display test (red, green, blue, white).
3. Verify backlight control works on BL pin.
4. Verify button inputs and stick ADC center/deadzone.
5. Draw one static sprite from flash.
6. Draw one animated sprite (4-frame loop).

Do not continue to gameplay until these pass.

## 5) Minimal Display Test (main.cpp)

Use this first, before engine code:

```cpp
#include <Arduino.h>

// Replace with your chosen display driver includes.
// #include "platform/display.hpp"

constexpr int PIN_BL = 13;

void setup() {
  Serial.begin(115200);

  ledcAttach(PIN_BL, 5000, 8);
  ledcWrite(PIN_BL, 255);

  // display_init();
  // display_fill(0xF800); delay(500);
  // display_fill(0x07E0); delay(500);
  // display_fill(0x001F); delay(500);
  // display_fill(0xFFFF); delay(500);
  // display_fill(0x0000); delay(500);
}

void loop() {
}
```

## 6) Memory Policy (Non-Negotiable)

- No per-frame dynamic allocations in update/render loops.
- Pre-allocate pools for:
  - entities
  - combat actions
  - UI widgets/cards
  - visual effects
- Keep hot frame buffers and transient draw state in internal RAM where possible.
- Keep atlases and large static content in PSRAM/flash.

## 7) Conversion Mapping (MicroPython -> C++)

Map old prototype components directly:

- show_guild_single_scene.py -> `scene_guild_home.cpp`
- build_guild_three_previews.py -> keep as PC-side asset pipeline tool
- st7735_1inch8.py -> `display_st7735.cpp`
- save JSON files -> binary or compact JSON in `save_slot.cpp`

## 8) First 10 Implementation Tasks

1. Board + display bring-up with color cycle.
2. Input bring-up (buttons + stick deadzone calibration).
3. Scene manager with two scenes (Boot, GuildHome).
4. GameState struct with one adventurer and needs.
5. Needs tick system (hunger/mood/energy decay).
6. Actions menu (feed/train/rest) with immediate stat changes.
7. Quest picker with 3 choices and reward outcome.
8. Recruit menu showing 4 generated candidates (data only first).
9. Unlock 2nd adventurer slot at rank gate.
10. Save/load slots and reboot persistence test.

## 9) Combat Entry Scope (After Core Loop)

- Start with 1v1 only.
- Then scale to 2v2.
- Then full target 4v3 with performance checks each step.
- Add bosses after 4v3 is stable.

## 10) Definition of Ready to Continue Content Build

Ready when all are true:

- Display stable for 30+ minutes without artifact/blackout.
- Inputs stable and debounced.
- Save/load reliable across power cycle.
- One-adventurer loop playable end-to-end.
- Frame pacing stable with one animated unit and UI active.
