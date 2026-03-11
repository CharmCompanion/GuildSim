"""Exact-pin test for Waveshare Pico-LCD-1.8 (ST7735S).

Pin map from Waveshare Pico-LCD-1.8 wiki:
- DIN  -> GP11
- CLK  -> GP10
- CS   -> GP9
- DC   -> GP8
- RST  -> GP12
- BL   -> GP13

Run on Pico with MicroPython.
"""

from machine import Pin, SPI, PWM  # type: ignore
import time

WIDTH = 128
HEIGHT = 160
X_OFFSET = 2
Y_OFFSET = 1


def rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


class LCD:
    def __init__(self):
        self.cs = Pin(9, Pin.OUT, value=1)
        self.dc = Pin(8, Pin.OUT, value=1)
        self.rst = Pin(12, Pin.OUT, value=1)

        self.bl_pwm = PWM(Pin(13))
        self.bl_pwm.freq(1000)
        self.bl_pwm.duty_u16(50000)

        self.spi = SPI(
            1,
            baudrate=40_000_000,
            polarity=0,
            phase=0,
            sck=Pin(10),
            mosi=Pin(11),
        )

    def cmd(self, c):
        self.cs(0)
        self.dc(0)
        self.spi.write(bytearray([c]))
        self.cs(1)

    def data(self, b):
        self.cs(0)
        self.dc(1)
        self.spi.write(b)
        self.cs(1)

    def data1(self, v):
        self.data(bytearray([v & 0xFF]))

    def reset(self):
        self.rst(1)
        time.sleep_ms(20)
        self.rst(0)
        time.sleep_ms(80)
        self.rst(1)
        time.sleep_ms(120)

    def init(self):
        self.reset()

        self.cmd(0x11)  # sleep out
        time.sleep_ms(120)

        self.cmd(0xB1)
        self.data(bytearray([0x01, 0x2C, 0x2D]))
        self.cmd(0xB2)
        self.data(bytearray([0x01, 0x2C, 0x2D]))
        self.cmd(0xB3)
        self.data(bytearray([0x01, 0x2C, 0x2D, 0x01, 0x2C, 0x2D]))

        self.cmd(0xB4)
        self.data1(0x07)

        self.cmd(0xC0)
        self.data(bytearray([0xA2, 0x02, 0x84]))
        self.cmd(0xC1)
        self.data1(0xC5)
        self.cmd(0xC2)
        self.data(bytearray([0x0A, 0x00]))
        self.cmd(0xC3)
        self.data(bytearray([0x8A, 0x2A]))
        self.cmd(0xC4)
        self.data(bytearray([0x8A, 0xEE]))

        self.cmd(0xC5)
        self.data1(0x0E)

        self.cmd(0x36)  # MADCTL
        self.data1(0xC8)

        self.cmd(0x3A)  # COLMOD RGB565
        self.data1(0x05)

        self.cmd(0xE0)
        self.data(bytearray([0x0F, 0x1A, 0x0F, 0x18, 0x2F, 0x28, 0x20, 0x22, 0x1F, 0x1B, 0x23, 0x37, 0x00, 0x07, 0x02, 0x10]))
        self.cmd(0xE1)
        self.data(bytearray([0x0F, 0x1B, 0x0F, 0x17, 0x33, 0x2C, 0x29, 0x2E, 0x30, 0x30, 0x39, 0x3F, 0x00, 0x07, 0x03, 0x10]))

        self.cmd(0x21)  # invert on
        self.cmd(0x29)  # display on
        time.sleep_ms(20)

    def window(self, x0, y0, x1, y1):
        x0 += X_OFFSET
        x1 += X_OFFSET
        y0 += Y_OFFSET
        y1 += Y_OFFSET

        self.cmd(0x2A)
        self.data(bytearray([0x00, x0 & 0xFF, 0x00, x1 & 0xFF]))

        self.cmd(0x2B)
        self.data(bytearray([0x00, y0 & 0xFF, 0x00, y1 & 0xFF]))

        self.cmd(0x2C)

    def fill(self, color):
        hi = (color >> 8) & 0xFF
        lo = color & 0xFF
        row = bytearray([hi, lo] * WIDTH)
        self.window(0, 0, WIDTH - 1, HEIGHT - 1)
        for _ in range(HEIGHT):
            self.data(row)


if __name__ == "__main__":
    lcd = LCD()
    lcd.init()

    palette = [
        ("black", rgb565(0, 0, 0)),
        ("white", rgb565(255, 255, 255)),
        ("gold", rgb565(212, 175, 55)),
        ("tan", rgb565(210, 180, 140)),
        ("brown", rgb565(101, 67, 33)),
        ("red", rgb565(220, 20, 20)),
        ("green", rgb565(20, 180, 70)),
        ("blue", rgb565(20, 70, 220)),
    ]

    print("Waveshare Pico-LCD-1.8 exact test start")
    for _ in range(3):
        for name, c in palette:
            print("fill:", name)
            lcd.fill(c)
            time.sleep_ms(700)
    print("Waveshare Pico-LCD-1.8 exact test done")
