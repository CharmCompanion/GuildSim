#pragma once

// ESP32-S3 DevKitC-1 N16R8 -> ST7735 1.8in wiring map
// Keep GPIO 26-32 unused (flash/PSRAM related on many N16R8 boards).

constexpr int PIN_TFT_MOSI = 11;
constexpr int PIN_TFT_SCLK = 12;
constexpr int PIN_TFT_CS   = 10;
constexpr int PIN_TFT_DC   = 9;
constexpr int PIN_TFT_RST  = 14;
constexpr int PIN_TFT_BL   = 21;

// Optional buttons
constexpr int PIN_BTN_A    = 4;
constexpr int PIN_BTN_B    = 5;
constexpr int PIN_BTN_MENU = 6;

// Optional PSP thumbstick
constexpr int PIN_STICK_X  = 1;  // ADC
constexpr int PIN_STICK_Y  = 2;  // ADC
constexpr int PIN_STICK_SW = 3;
