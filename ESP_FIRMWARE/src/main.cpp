#include <Arduino.h>
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7735.h>
#include <esp_heap_caps.h>

#include "pins.h"

#ifndef TFT_TAB_PROFILE
#define TFT_TAB_PROFILE 0
#endif

#if TFT_TAB_PROFILE == 1
#define TFT_INIT_PROFILE INITR_GREENTAB
static const char *kTabLabel = "GREENTAB";
#elif TFT_TAB_PROFILE == 2
#define TFT_INIT_PROFILE INITR_REDTAB
static const char *kTabLabel = "REDTAB";
#else
#define TFT_INIT_PROFILE INITR_BLACKTAB
static const char *kTabLabel = "BLACKTAB";
#endif

// ST7735 128x160 controller
Adafruit_ST7735 tft(PIN_TFT_CS, PIN_TFT_DC, PIN_TFT_MOSI, PIN_TFT_SCLK, PIN_TFT_RST);

struct StickFilter {
  int center_x = 0;
  int center_y = 0;
  float filtered_x = 0.0f;
  float filtered_y = 0.0f;
};

static StickFilter g_stick;
static int g_cursor_x = 64;
static int g_cursor_y = 100;

static void set_backlight(uint8_t duty) {
  constexpr uint8_t kBacklightChannel = 0;
  ledcSetup(kBacklightChannel, 5000, 8);
  ledcAttachPin(PIN_TFT_BL, kBacklightChannel);
  ledcWrite(kBacklightChannel, duty);
}

static void draw_boot_report() {
  tft.fillScreen(ST77XX_BLACK);
  tft.setTextWrap(false);
  tft.setTextColor(ST77XX_WHITE);
  tft.setTextSize(1);
  tft.setCursor(2, 6);
  tft.print("Guildmaster ESP Boot");

  tft.setCursor(2, 22);
  tft.print("Heap: ");
  tft.print(ESP.getFreeHeap());

  tft.setCursor(2, 34);
  tft.print("PSRAM: ");
  if (psramFound()) {
    tft.print(ESP.getPsramSize());
  } else {
    tft.print("NOT FOUND");
  }

  tft.setCursor(2, 46);
  tft.print("Flash: ");
  tft.print(ESP.getFlashChipSize());

  tft.setCursor(2, 58);
  tft.print("Tab: ");
  tft.print(kTabLabel);
}

static int apply_deadzone(int raw, int center, int deadzone) {
  int delta = raw - center;
  if (abs(delta) <= deadzone) {
    return 0;
  }
  return delta;
}

static void calibrate_stick_center() {
  constexpr int kSamples = 64;
  long sum_x = 0;
  long sum_y = 0;
  for (int i = 0; i < kSamples; ++i) {
    sum_x += analogRead(PIN_STICK_X);
    sum_y += analogRead(PIN_STICK_Y);
    delay(4);
  }
  g_stick.center_x = static_cast<int>(sum_x / kSamples);
  g_stick.center_y = static_cast<int>(sum_y / kSamples);
  g_stick.filtered_x = 0.0f;
  g_stick.filtered_y = 0.0f;
}

static void draw_guild_screen_shell() {
  tft.fillScreen(ST77XX_BLACK);
  tft.setTextWrap(false);
  tft.setTextSize(1);

  tft.drawRect(0, 0, 128, 160, ST77XX_WHITE);
  tft.fillRect(1, 1, 126, 16, ST77XX_BLUE);
  tft.setTextColor(ST77XX_WHITE);
  tft.setCursor(8, 6);
  tft.print("GUILDMASTER");

  tft.drawRect(4, 24, 120, 62, ST77XX_WHITE);
  tft.setTextColor(ST77XX_GREEN);
  tft.setCursor(8, 30);
  tft.print("Guild Hall");
  tft.setTextColor(ST77XX_WHITE);
  tft.setCursor(8, 44);
  tft.print("Members: 4");
  tft.setCursor(8, 56);
  tft.print("Supplies: 82");
  tft.setCursor(8, 68);
  tft.print("Morale: High");

  tft.drawRect(4, 92, 120, 46, ST77XX_WHITE);
  tft.setTextColor(ST77XX_CYAN);
  tft.setCursor(8, 98);
  tft.print("Stick to move cursor");
  tft.setTextColor(ST77XX_WHITE);
  tft.setCursor(8, 110);
  tft.print("A: Select");
  tft.setCursor(8, 122);
  tft.print("B: Back");

  tft.setTextColor(ST77XX_YELLOW);
  tft.setCursor(8, 146);
  tft.print("MENU: Mission Log");
}

static void draw_cursor(int x, int y, uint16_t color) {
  tft.drawFastHLine(x - 2, y, 5, color);
  tft.drawFastVLine(x, y - 2, 5, color);
}

void setup() {
  Serial.begin(115200);
  uint32_t serial_wait_start = millis();
  while (!Serial && (millis() - serial_wait_start) < 3000) {
    delay(10);
  }

  Serial.println("[BOOT] setup start");

  Serial.println("[BOOT] backlight init");
  set_backlight(255);

  // Hardware SPI init on selected pins.
  Serial.println("[BOOT] SPI begin");
  SPI.begin(PIN_TFT_SCLK, -1, PIN_TFT_MOSI, PIN_TFT_CS);

  Serial.println("[BOOT] TFT initR begin");
  tft.initR(TFT_INIT_PROFILE);
  Serial.println("[BOOT] TFT initR done");

  tft.setRotation(2);  // portrait/upright; adjust if needed
  Serial.println("[BOOT] rotation set");

  draw_boot_report();
  Serial.println("[BOOT] report drawn");

  pinMode(PIN_BTN_A, INPUT_PULLUP);
  pinMode(PIN_BTN_B, INPUT_PULLUP);
  pinMode(PIN_BTN_MENU, INPUT_PULLUP);
  pinMode(PIN_STICK_SW, INPUT_PULLUP);

  analogReadResolution(12);
  calibrate_stick_center();
  draw_guild_screen_shell();
  draw_cursor(g_cursor_x, g_cursor_y, ST77XX_YELLOW);

  Serial.printf("[BOOT] stick center x=%d y=%d\n", g_stick.center_x, g_stick.center_y);

  Serial.println("[BOOT] setup complete");
}

void loop() {
  static uint32_t last_move = 0;
  static uint32_t last_status = 0;
  if (millis() - last_move >= 33) {
    last_move = millis();

    constexpr int kDeadzone = 120;
    int raw_x = analogRead(PIN_STICK_X);
    int raw_y = analogRead(PIN_STICK_Y);

    int delta_x = apply_deadzone(raw_x, g_stick.center_x, kDeadzone);
    int delta_y = apply_deadzone(raw_y, g_stick.center_y, kDeadzone);

    g_stick.filtered_x = (g_stick.filtered_x * 0.75f) + (static_cast<float>(delta_x) * 0.25f);
    g_stick.filtered_y = (g_stick.filtered_y * 0.75f) + (static_cast<float>(delta_y) * 0.25f);

    int move_x = static_cast<int>(g_stick.filtered_x / 320.0f);
    int move_y = static_cast<int>(g_stick.filtered_y / 320.0f);
    if (abs(move_x) < 1) move_x = 0;
    if (abs(move_y) < 1) move_y = 0;

    if (move_x != 0 || move_y != 0) {
      draw_cursor(g_cursor_x, g_cursor_y, ST77XX_BLACK);
      g_cursor_x = constrain(g_cursor_x + move_x, 8, 120);
      g_cursor_y = constrain(g_cursor_y + move_y, 28, 152);
      draw_cursor(g_cursor_x, g_cursor_y, ST77XX_YELLOW);
    }
  }

  if (millis() - last_status >= 1000) {
    last_status = millis();
    Serial.printf("guild screen active; cursor=(%d,%d) a=%d b=%d menu=%d\n",
      g_cursor_x,
      g_cursor_y,
      digitalRead(PIN_BTN_A) == LOW,
      digitalRead(PIN_BTN_B) == LOW,
      digitalRead(PIN_BTN_MENU) == LOW);
  }
}
