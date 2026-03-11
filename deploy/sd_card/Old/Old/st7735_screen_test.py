"""ST7735/ST7789 probe for Pico W.

Runs multiple common pin mappings + init variants to identify what your LCD uses.
Watch the physical screen while this runs and note which PROFILE+MODE shows colors.
"""

import time

from machine import Pin, SPI  # type: ignore

WIDTH = 128
HEIGHT = 160

# Common Pico wiring used in this project.
PROFILE_SPI0_GENERIC = {
    "name": "spi0_generic",
    "spi_id": 0,
    "sck": 18,
    "mosi": 19,
    "miso": 16,
    "cs": 17,
    "dc": 20,
    "rst": 21,
    "bl": 22,
    "baud": 20_000_000,
}

# Common 1.8 inch Pico LCD hat style (ST7735 family) on SPI1.
PROFILE_SPI1_LCDHAT = {
    "name": "spi1_lcdhat",
    "spi_id": 1,
    "sck": 10,
    "mosi": 11,
    "miso": 12,
    "cs": 9,
    "dc": 8,
    "rst": 15,
    "bl": 13,
    "baud": 40_000_000,
}

# Common Waveshare Pico-LCD-1.8 map (ST7735S)
PROFILE_SPI1_WAVESHARE = {
    "name": "spi1_waveshare_1p8",
    "spi_id": 1,
    "sck": 10,
    "mosi": 11,
    "miso": None,
    "cs": 9,
    "dc": 8,
    "rst": 12,
    "bl": 13,
    "baud": 40_000_000,
}

PROFILES = [PROFILE_SPI0_GENERIC, PROFILE_SPI1_LCDHAT, PROFILE_SPI1_WAVESHARE]


def rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


PALETTE = [
    ("black", rgb565(0, 0, 0)),
    ("tan", rgb565(210, 180, 140)),
    ("brown", rgb565(101, 67, 33)),
    ("gold", rgb565(212, 175, 55)),
    ("white", rgb565(255, 255, 255)),
    ("red", rgb565(220, 20, 20)),
    ("green", rgb565(20, 180, 70)),
    ("blue", rgb565(20, 70, 220)),
]


class LCD:
    def __init__(self, cfg):
        self.cfg = cfg
        self.cs = Pin(cfg["cs"], Pin.OUT, value=1)
        self.dc = Pin(cfg["dc"], Pin.OUT, value=1)
        self.rst = Pin(cfg["rst"], Pin.OUT, value=1)
        self.bl = Pin(cfg["bl"], Pin.OUT, value=1) if cfg.get("bl") is not None else None

        spi_kwargs = {
            "baudrate": cfg["baud"],
            "polarity": 0,
            "phase": 0,
            "bits": 8,
            "firstbit": SPI.MSB,
            "sck": Pin(cfg["sck"]),
            "mosi": Pin(cfg["mosi"]),
        }
        if cfg.get("miso") is not None:
            spi_kwargs["miso"] = Pin(cfg["miso"])

        self.spi = SPI(cfg["spi_id"], **spi_kwargs)

    def _cmd(self, c):
        self.cs(0)
        self.dc(0)
        self.spi.write(bytearray([c]))
        self.cs(1)

    def _data(self, buf):
        self.cs(0)
        self.dc(1)
        self.spi.write(buf)
        self.cs(1)

    def backlight_blink(self):
        if self.bl is None:
            return
        for _ in range(2):
            self.bl(0)
            time.sleep_ms(150)
            self.bl(1)
            time.sleep_ms(150)

    def reset(self):
        self.rst(1)
        time.sleep_ms(30)
        self.rst(0)
        time.sleep_ms(120)
        self.rst(1)
        time.sleep_ms(120)

    def init_mode(self, mode):
        self.reset()

        self._cmd(0x01)  # SWRESET
        time.sleep_ms(150)
        self._cmd(0x11)  # SLPOUT
        time.sleep_ms(150)

        self._cmd(0x3A)  # COLMOD
        if mode in ("st7735_rgb", "st7735_bgr", "st7789_like"):
            self._data(bytearray([0x55]))  # RGB565 (standard DCS value)
        else:
            self._data(bytearray([0x66]))  # RGB666 (standard DCS value)

        # MADCTL variants (RGB/BGR + rotation hints)
        if mode == "st7735_rgb":
            self._cmd(0x36)
            self._data(bytearray([0x00]))
        elif mode == "st7735_bgr":
            self._cmd(0x36)
            self._data(bytearray([0x08]))
        elif mode == "st7789_like":
            self._cmd(0x36)
            self._data(bytearray([0x70]))
        elif mode == "waveshare_st7735":
            # Common for Pico-LCD style ST7735S modules.
            self._cmd(0x36)
            self._data(bytearray([0xC8]))

        # Basic power/frame setup that works for many ST7735S modules.
        self._cmd(0xB1)
        self._data(bytearray([0x01, 0x2C, 0x2D]))
        self._cmd(0xB2)
        self._data(bytearray([0x01, 0x2C, 0x2D]))
        self._cmd(0xB3)
        self._data(bytearray([0x01, 0x2C, 0x2D, 0x01, 0x2C, 0x2D]))
        self._cmd(0xB4)
        self._data(bytearray([0x07]))

        self._cmd(0xC0)
        self._data(bytearray([0xA2, 0x02, 0x84]))
        self._cmd(0xC1)
        self._data(bytearray([0xC5]))
        self._cmd(0xC2)
        self._data(bytearray([0x0A, 0x00]))
        self._cmd(0xC3)
        self._data(bytearray([0x8A, 0x2A]))
        self._cmd(0xC4)
        self._data(bytearray([0x8A, 0xEE]))
        self._cmd(0xC5)
        self._data(bytearray([0x0E]))

        self._cmd(0x29)  # DISPON
        time.sleep_ms(100)

        if self.bl is not None:
            self.bl(1)

    def _set_window(self, x0, y0, x1, y1):
        self._cmd(0x2A)
        self._data(bytearray([0x00, x0 & 0xFF, 0x00, x1 & 0xFF]))
        self._cmd(0x2B)
        self._data(bytearray([0x00, y0 & 0xFF, 0x00, y1 & 0xFF]))
        self._cmd(0x2C)

    def fill565(self, color565, byte_swap=False):
        hi = (color565 >> 8) & 0xFF
        lo = color565 & 0xFF
        self._set_window(0, 0, WIDTH - 1, HEIGHT - 1)
        if byte_swap:
            row = bytearray([lo, hi] * WIDTH)
        else:
            row = bytearray([hi, lo] * WIDTH)
        for _ in range(HEIGHT):
            self._data(row)

    def fill666(self, r, g, b):
        self._set_window(0, 0, WIDTH - 1, HEIGHT - 1)
        r6 = r & 0xFC
        g6 = g & 0xFC
        b6 = b & 0xFC
        pix = bytearray([r6, g6, b6])
        row = pix * WIDTH
        for _ in range(HEIGHT):
            self._data(row)


def run_probe():
    modes = [
        "st7735_rgb",
        "st7735_bgr",
        "waveshare_st7735",
        "st7789_like",
        "rgb666_rgb",
        "rgb666_bgr",
    ]

    print("Starting LCD probe. Watch the physical screen.")
    print("If you see colors on any pass, note PROFILE+MODE.")

    for profile in PROFILES:
        for mode in modes:
            print("PROBE profile={} mode={}".format(profile["name"], mode))
            try:
                lcd = LCD(profile)
                lcd.backlight_blink()
                lcd.init_mode(mode)

                for name, color in PALETTE:
                    print("fill:", name)
                    if mode.startswith("rgb666"):
                        # Use explicit RGB channels for 18-bit test path.
                        mapping = {
                            "black": (0, 0, 0),
                            "tan": (210, 180, 140),
                            "brown": (101, 67, 33),
                            "gold": (212, 175, 55),
                            "white": (255, 255, 255),
                            "red": (220, 20, 20),
                            "green": (20, 180, 70),
                            "blue": (20, 70, 220),
                        }
                        r, g, b = mapping[name]
                        if mode.endswith("bgr"):
                            lcd.fill666(b, g, r)
                        else:
                            lcd.fill666(r, g, b)
                    else:
                        # Test both endian orders for RGB565 payload writes.
                        lcd.fill565(color, byte_swap=False)
                    time.sleep_ms(450)

                if not mode.startswith("rgb666"):
                    print("repeat with RGB565 byte swap")
                    for name, color in PALETTE:
                        print("fill-swapped:", name)
                        lcd.fill565(color, byte_swap=True)
                        time.sleep_ms(350)

            except Exception as exc:
                print("probe failed:", exc)

    print("Probe complete.")


if __name__ == "__main__":
    run_probe()
