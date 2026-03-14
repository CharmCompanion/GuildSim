# Hardware Profiles (Your Parts)

This project now supports board/peripheral profiles through `hardware_profiles.py`.

Set profile in REPL:

```python
import sys
sys.path.append('/Core')
from hardware_runtime import set_profile
set_profile('pico_w_terminal')
```

Current options:

- `pico_w_terminal`
- `pico_w_lcd_1_8`
- `esp32_c6_touch`
- `pi_zero_w_companion`
- `esp8266mod_companion`

## Your Listed Hardware Mapping

1. Raspberry Pi Pico W
- Primary supported board for current MicroPython runtime.

2. Raspberry Pi Zero W
- Use as Linux companion/controller if desired (not same MicroPython deployment target).

3. MAX98357A I2S 3W amp + 13mm 8ohm speaker
- ESP32-C6 profile: native I2S path expected.
- Pico W profile: requires software/PIO I2S implementation (future audio module step).

4. ALPS SKRHABE010 5-way tact switch
- Supported as GPIO input concept in Pico profiles.

5. ESP32-C6 with 1.3 IPS touch + SD
- Profile included for migration planning (`esp32_c6_touch`).

6. Waveshare Pico-LCD-1.8 SPI
- Pico profile included (`pico_w_lcd_1_8`) for display-target configuration.

7. LiPo 1200mAh / 2000mAh
- Power hardware is external to firmware logic. Use regulator/protection board as required.

8. ESP8266MOD
- Companion/network helper profile included (`esp8266mod_companion`).

## Notes

- Profile selection currently controls diagnostics/config metadata and deployment intent.
- Functional drivers for LCD/touch/audio can now be added behind this profile layer without refactoring game logic.
