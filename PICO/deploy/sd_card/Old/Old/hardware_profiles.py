"""Hardware profile definitions for supported boards and peripherals."""

PROFILES = {
    "pico_w_terminal": {
        "board": "Raspberry Pi Pico W",
        "display": "Thonny serial terminal",
        "storage": "SPI SD module",
        "audio": "optional MAX98357A via software/PIO I2S",
        "input": "USB keyboard input in terminal",
        "wireless": "onboard Wi-Fi",
        "pins": {
            "sd_spi0": {"miso": 16, "cs": 17, "sck": 18, "mosi": 19},
            "tact_5way": "map to GPIO interrupts (user-defined)",
            "max98357a_i2s": "PIO I2S required on RP2040",
        },
    },
    "pico_w_lcd_1_8": {
        "board": "Raspberry Pi Pico W",
        "display": "Waveshare Pico-LCD-1.8 (SPI)",
        "storage": "SPI SD module",
        "audio": "optional MAX98357A via software/PIO I2S",
        "input": "ALPS SKRHABE010 5-way tact switch",
        "wireless": "onboard Wi-Fi",
        "pins": {
            "sd_spi0": {"miso": 16, "cs": 17, "sck": 18, "mosi": 19},
            "lcd": "Waveshare default Pico-LCD-1.8 pin map",
            "tact_5way": "GPIO digital inputs",
        },
    },
    "esp32_c6_touch": {
        "board": "ESP32-C6",
        "display": "1.3 IPS touchscreen",
        "storage": "onboard SD slot",
        "audio": "MAX98357A native I2S",
        "input": "touchscreen + optional tact switch",
        "wireless": "Wi-Fi 6 + BLE 5",
        "pins": {
            "sd": "board-specific SD slot",
            "i2s": "board-specific I2S pins",
            "touch": "board-specific touch controller",
        },
    },
    "pi_zero_w_companion": {
        "board": "Raspberry Pi Zero W",
        "display": "HDMI/TFT depending setup",
        "storage": "Linux filesystem",
        "audio": "PWM/I2S via Linux stack",
        "input": "USB/Bluetooth controller or keyboard",
        "wireless": "Wi-Fi + BLE",
        "pins": {
            "role": "companion UI/server, not MicroPython target",
        },
    },
    "esp8266mod_companion": {
        "board": "ESP8266MOD",
        "display": "none",
        "storage": "flash only",
        "audio": "not recommended for game audio",
        "input": "none",
        "wireless": "Wi-Fi",
        "pins": {
            "role": "network helper/bridge only",
        },
    },
}

DEFAULT_PROFILE = "pico_w_terminal"
