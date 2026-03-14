"""Deep LCD probe for Pico SPI TFT modules.

Tries multiple controller init families and geometry assumptions.
Watch the physical LCD and note the first CASE line that shows real colors.
"""

import time
from machine import Pin, SPI  # type: ignore


def rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


CASES = [
    {
        "name": "waveshare_spi1_st7735_128x160",
        "spi_id": 1,
        "sck": 10,
        "mosi": 11,
        "cs": 9,
        "dc": 8,
        "rst": 12,
        "bl": 13,
        "baud": 40_000_000,
        "driver": "st7735",
        "w": 128,
        "h": 160,
        "xoff": 0,
        "yoff": 0,
        "madctl": 0xC8,
    },
    {
        "name": "waveshare_spi1_st7735_128x160_offset",
        "spi_id": 1,
        "sck": 10,
        "mosi": 11,
        "cs": 9,
        "dc": 8,
        "rst": 12,
        "bl": 13,
        "baud": 40_000_000,
        "driver": "st7735",
        "w": 128,
        "h": 160,
        "xoff": 2,
        "yoff": 1,
        "madctl": 0xC8,
    },
    {
        "name": "waveshare_spi1_st7789_240x240",
        "spi_id": 1,
        "sck": 10,
        "mosi": 11,
        "cs": 9,
        "dc": 8,
        "rst": 12,
        "bl": 13,
        "baud": 62_500_000,
        "driver": "st7789",
        "w": 240,
        "h": 240,
        "xoff": 0,
        "yoff": 0,
        "madctl": 0x00,
    },
    {
        "name": "spi0_alt_st7735_128x160",
        "spi_id": 0,
        "sck": 18,
        "mosi": 19,
        "cs": 17,
        "dc": 20,
        "rst": 21,
        "bl": 22,
        "baud": 20_000_000,
        "driver": "st7735",
        "w": 128,
        "h": 160,
        "xoff": 0,
        "yoff": 0,
        "madctl": 0x00,
    },
]


class TFT:
    def __init__(self, c):
        self.c = c
        self.cs = Pin(c["cs"], Pin.OUT, value=1)
        self.dc = Pin(c["dc"], Pin.OUT, value=1)
        self.rst = Pin(c["rst"], Pin.OUT, value=1)
        self.bl = Pin(c["bl"], Pin.OUT, value=1)
        self.spi = SPI(
            c["spi_id"],
            baudrate=c["baud"],
            polarity=0,
            phase=0,
            bits=8,
            firstbit=SPI.MSB,
            sck=Pin(c["sck"]),
            mosi=Pin(c["mosi"]),
        )

    def cmd(self, v):
        self.cs(0)
        self.dc(0)
        self.spi.write(bytearray([v]))
        self.cs(1)

    def data(self, b):
        self.cs(0)
        self.dc(1)
        self.spi.write(b)
        self.cs(1)

    def reset(self):
        self.bl(0)
        time.sleep_ms(80)
        self.bl(1)
        time.sleep_ms(80)
        self.rst(1)
        time.sleep_ms(20)
        self.rst(0)
        time.sleep_ms(120)
        self.rst(1)
        time.sleep_ms(120)

    def init(self):
        self.reset()
        if self.c["driver"] == "st7789":
            self._init_st7789()
        else:
            self._init_st7735()

    def _init_st7735(self):
        self.cmd(0x01)
        time.sleep_ms(150)
        self.cmd(0x11)
        time.sleep_ms(150)
        self.cmd(0x3A)
        self.data(bytearray([0x55]))
        self.cmd(0x36)
        self.data(bytearray([self.c["madctl"]]))
        self.cmd(0x21)  # inversion on
        self.cmd(0x29)
        time.sleep_ms(100)

    def _init_st7789(self):
        self.cmd(0x01)
        time.sleep_ms(150)
        self.cmd(0x11)
        time.sleep_ms(150)
        self.cmd(0x3A)
        self.data(bytearray([0x55]))
        self.cmd(0x36)
        self.data(bytearray([self.c["madctl"]]))
        self.cmd(0x21)
        self.cmd(0x29)
        time.sleep_ms(100)

    def set_window(self, x0, y0, x1, y1):
        x0 += self.c.get("xoff", 0)
        x1 += self.c.get("xoff", 0)
        y0 += self.c.get("yoff", 0)
        y1 += self.c.get("yoff", 0)
        self.cmd(0x2A)
        self.data(bytearray([x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF]))
        self.cmd(0x2B)
        self.data(bytearray([y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF]))
        self.cmd(0x2C)

    def fill(self, color, swap=False):
        w = self.c["w"]
        h = self.c["h"]
        self.set_window(0, 0, w - 1, h - 1)
        hi = (color >> 8) & 0xFF
        lo = color & 0xFF
        if swap:
            row = bytearray([lo, hi] * w)
        else:
            row = bytearray([hi, lo] * w)
        for _ in range(h):
            self.data(row)


def run_probe():
    colors = [
        ("black", rgb565(0, 0, 0)),
        ("white", rgb565(255, 255, 255)),
        ("gold", rgb565(212, 175, 55)),
        ("tan", rgb565(210, 180, 140)),
        ("brown", rgb565(101, 67, 33)),
        ("red", rgb565(220, 20, 20)),
        ("green", rgb565(20, 180, 70)),
        ("blue", rgb565(20, 70, 220)),
    ]

    print("Deep probe start")
    print("Watch LCD and note first CASE that shows real colors")

    for case in CASES:
        print("CASE:", case["name"])
        try:
            lcd = TFT(case)
            lcd.init()

            print("normal endian")
            for name, c in colors:
                print("  ", name)
                lcd.fill(c, swap=False)
                time.sleep_ms(350)

            print("swapped endian")
            for name, c in colors:
                print("  ", name)
                lcd.fill(c, swap=True)
                time.sleep_ms(250)

        except Exception as exc:
            print("case failed:", exc)

    print("Deep probe done")


if __name__ == "__main__":
    run_probe()
