from machine import I2C, Pin  # pyright: ignore[reportMissingImports]
import time


class ADS7830Joystick:
    """Read joystick axes over ADS7830 and edge-triggered A/B button events."""

    _CH_MAP = [0, 4, 1, 5, 2, 6, 3, 7]

    def __init__(
        self,
        i2c_id=0,
        sda_pin=4,
        scl_pin=5,
        adc_addr=0x48,
        x_channel=0,
        y_channel=1,
        stick_pin=14,
        a_pin=15,
        b_pin=16,
    ):
        self.i2c = I2C(i2c_id, sda=Pin(sda_pin), scl=Pin(scl_pin))
        self.addr = adc_addr
        self.x_channel = x_channel
        self.y_channel = y_channel

        self.btn_stick = Pin(stick_pin, Pin.IN, Pin.PULL_UP)
        self.btn_a = Pin(a_pin, Pin.IN, Pin.PULL_UP)
        self.btn_b = Pin(b_pin, Pin.IN, Pin.PULL_UP)

        self.center_x = 128
        self.center_y = 128
        self.deadzone = 28
        self.repeat_ms = 180

        self._last_repeat = time.ticks_ms()
        self._prev = {"a": False, "b": False, "stick": False}

    def _read_channel(self, channel):
        ch = self._CH_MAP[channel & 0x07]
        cmd = 0x84 | (ch << 4)
        try:
            self.i2c.writeto(self.addr, bytes([cmd]))
            return self.i2c.readfrom(self.addr, 1)[0]
        except Exception:
            return 128

    def read_raw(self):
        x = self._read_channel(self.x_channel)
        y = self._read_channel(self.y_channel)
        stick = not self.btn_stick.value()
        a = not self.btn_a.value()
        b = not self.btn_b.value()
        return x, y, stick, a, b

    def calibrate_center(self, samples=24, delay_ms=10):
        sx = 0
        sy = 0
        for _ in range(samples):
            x, y, _, _, _ = self.read_raw()
            sx += x
            sy += y
            time.sleep_ms(delay_ms)
        self.center_x = sx // samples
        self.center_y = sy // samples

    def _direction_now(self, x, y):
        left = x < (self.center_x - self.deadzone)
        right = x > (self.center_x + self.deadzone)
        up = y < (self.center_y - self.deadzone)
        down = y > (self.center_y + self.deadzone)
        return left, right, up, down

    def poll(self):
        """Return one-shot input events suitable for menu navigation."""
        x, y, stick, a, b = self.read_raw()
        left, right, up, down = self._direction_now(x, y)

        now = time.ticks_ms()
        can_repeat = time.ticks_diff(now, self._last_repeat) >= self.repeat_ms
        move = None

        if can_repeat and (left or right or up or down):
            self._last_repeat = now
            dx = x - self.center_x
            dy = y - self.center_y
            abs_dx = dx if dx >= 0 else -dx
            abs_dy = dy if dy >= 0 else -dy

            # Use dominant axis so horizontal tab switching is not blocked by vertical noise.
            if abs_dx > abs_dy:
                if left:
                    move = "left"
                elif right:
                    move = "right"
            else:
                if up:
                    move = "up"
                elif down:
                    move = "down"

            # Fallback if dominant-axis decision produced no move.
            if move is None:
                if up:
                    move = "up"
                elif down:
                    move = "down"
                elif left:
                    move = "left"
                elif right:
                    move = "right"

        events = {
            "move": move,
            "a_pressed": (a and not self._prev["a"]),
            "b_pressed": (b and not self._prev["b"]),
            "stick_pressed": (stick and not self._prev["stick"]),
            "raw_x": x,
            "raw_y": y,
        }

        self._prev["a"] = a
        self._prev["b"] = b
        self._prev["stick"] = stick
        return events
