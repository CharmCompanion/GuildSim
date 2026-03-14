from machine import Pin, PWM
import time
import lcd

# Button mapping
BTN_DOWN_PIN = 14
BTN_SELECT_PIN = 15
BTN_BACK_PIN = 16

COL_BG = 0x0000
COL_TEXT = 0xFFFF
COL_OK = 0x07E0
COL_HIT = 0xF800


class DebouncedButton:
    def __init__(self, pin, debounce_ms=8, cooldown_ms=0):
        self.pin = pin
        self.debounce_ms = debounce_ms
        self.cooldown_ms = cooldown_ms
        self.raw_state = self.pin.value() == 0
        self.stable_state = self.raw_state
        self.last_change_ms = time.ticks_ms()
        self.last_press_ms = time.ticks_ms()

    def update(self):
        now = time.ticks_ms()
        raw = self.pin.value() == 0

        if raw != self.raw_state:
            self.raw_state = raw
            self.last_change_ms = now

        pressed_event = False
        if time.ticks_diff(now, self.last_change_ms) >= self.debounce_ms:
            if self.stable_state != self.raw_state:
                self.stable_state = self.raw_state
                if self.stable_state and time.ticks_diff(now, self.last_press_ms) >= self.cooldown_ms:
                    self.last_press_ms = now
                    pressed_event = True

        return self.stable_state, pressed_event


class ButtonTestScreen:
    def __init__(self):
        self.bl = PWM(Pin(13))
        self.bl.freq(1000)
        self.bl.duty_u16(56000)

        self.d = lcd.LCD_1inch8()

        self.btn_down = DebouncedButton(Pin(BTN_DOWN_PIN, Pin.IN, Pin.PULL_UP))
        self.btn_select = DebouncedButton(Pin(BTN_SELECT_PIN, Pin.IN, Pin.PULL_UP))
        self.btn_back = DebouncedButton(Pin(BTN_BACK_PIN, Pin.IN, Pin.PULL_UP))

        self.down_count = 0
        self.select_count = 0
        self.back_count = 0

        self.down_prev = False
        self.select_prev = False
        self.back_prev = False

    def draw(self, down_now, select_now, back_now):
        self.d.fill(COL_BG)

        self.d.text("BUTTON TEST", 20, 8, COL_TEXT)
        self.d.text("Pins: D14 S15 B16", 8, 20, COL_TEXT)

        self._draw_row(36, "DOWN", down_now, self.down_count)
        self._draw_row(56, "SELECT", select_now, self.select_count)
        self._draw_row(76, "BACK", back_now, self.back_count)

        if self.down_count and self.select_count and self.back_count:
            self.d.text("ALL BUTTONS WORK", 8, 100, COL_OK)
        else:
            self.d.text("Press each button", 14, 100, COL_TEXT)

        self.d.text("Hold BACK 2s to exit", 6, 116, COL_TEXT)
        self.d.show()

    def _draw_row(self, y, name, is_down, count):
        state = "PRESSED" if is_down else "released"
        color = COL_HIT if is_down else COL_OK
        self.d.text("{}: {}".format(name, state), 8, y, color)
        self.d.text("count:{}".format(count), 106, y, COL_TEXT)

    def run(self):
        back_hold_start = None

        while True:
            down_now, down_pressed = self.btn_down.update()
            select_now, select_pressed = self.btn_select.update()
            back_now, back_pressed = self.btn_back.update()

            if down_pressed:
                self.down_count += 1
            if select_pressed:
                self.select_count += 1
            if back_pressed:
                self.back_count += 1

            self.down_prev = down_now
            self.select_prev = select_now
            self.back_prev = back_now

            # Hold BACK to exit test screen.
            if back_now:
                if back_hold_start is None:
                    back_hold_start = time.ticks_ms()
                elif time.ticks_diff(time.ticks_ms(), back_hold_start) >= 2000:
                    self.d.fill(COL_BG)
                    self.d.text("Exiting...", 40, 58, COL_TEXT)
                    self.d.show()
                    time.sleep_ms(400)
                    return
            else:
                back_hold_start = None

            self.draw(down_now, select_now, back_now)
            time.sleep_ms(10)


def main():
    ButtonTestScreen().run()


if __name__ == "__main__":
    main()
