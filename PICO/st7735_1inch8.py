from machine import Pin, SPI  # pyright: ignore[reportMissingImports]
import framebuf  # pyright: ignore[reportMissingImports]
import time


class LCD_1inch8(framebuf.FrameBuffer):
    """Waveshare-style 1.8in ST7735S driver for Pico (SPI1).

    Pin map:
    - DIN  -> GP11
    - CLK  -> GP10
    - CS   -> GP9
    - DC   -> GP8
    - RST  -> GP12
    - BL   -> GP13 (handled in main script)
    """

    def __init__(self):
        self.width = 128
        self.height = 160

        self.cs = Pin(9, Pin.OUT)
        self.rst = Pin(12, Pin.OUT)
        self.dc = Pin(8, Pin.OUT)

        # Optional touch CS pin on some boards.
        self.tp_cs = Pin(7, Pin.OUT)
        self.tp_cs.value(1)

        self.spi = SPI(
            1,
            # Keep conservative for jumper-wire stability.
            baudrate=10_000_000,
            polarity=0,
            phase=0,
            sck=Pin(10),
            mosi=Pin(11),
            miso=None,
        )

        self.buffer = bytearray(self.height * self.width * 2)
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)

        self.red = 0xF800
        self.green = 0x07E0
        self.blue = 0x001F
        self.white = 0xFFFF
        self.black = 0x0000
        self.gold = 0xD5A0
        self.tan = 0xD5B1
        self.brown = 0x6186

        self.init_display()
        # Blast a clean black frame immediately to kill power-on snow.
        self.fill(0x0000)
        self.show()

    def write_cmd(self, cmd):
        self.cs(1)
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, val):
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(bytearray([val]))
        self.cs(1)

    def init_display(self):
        # Software reset helps recover panels that come up in a bad state.
        self.write_cmd(0x01)
        time.sleep_ms(150)

        self.rst(1)
        time.sleep_ms(120)
        self.rst(0)
        time.sleep_ms(120)
        self.rst(1)
        time.sleep_ms(180)

        self.write_cmd(0x36)
        # MY=1, MX=1 = 180° portrait (upright).  BGR=0 = RGB colour order.
        self.write_data(0xC0)

        self.write_cmd(0x3A)
        self.write_data(0x05)

        self.write_cmd(0xB2)
        self.write_data(0x0C)
        self.write_data(0x0C)
        self.write_data(0x00)
        self.write_data(0x33)
        self.write_data(0x33)

        self.write_cmd(0xB7)
        self.write_data(0x35)

        self.write_cmd(0xBB)
        self.write_data(0x19)

        self.write_cmd(0xC0)
        self.write_data(0x2C)

        self.write_cmd(0xC2)
        self.write_data(0x01)

        self.write_cmd(0xC3)
        self.write_data(0x12)

        self.write_cmd(0xC4)
        self.write_data(0x20)

        self.write_cmd(0xC6)
        self.write_data(0x0F)

        self.write_cmd(0xD0)
        self.write_data(0xA4)
        self.write_data(0xA1)

        self.write_cmd(0xE0)
        for v in (0xD0, 0x04, 0x0D, 0x11, 0x13, 0x2B, 0x3F, 0x54, 0x4C, 0x18, 0x0D, 0x0B, 0x1F, 0x23):
            self.write_data(v)

        self.write_cmd(0xE1)
        for v in (0xD0, 0x04, 0x0C, 0x11, 0x13, 0x2C, 0x3F, 0x44, 0x51, 0x2F, 0x1F, 0x1F, 0x20, 0x23):
            self.write_data(v)

        # Inversion OFF: use direct colour path for stable tone mapping.
        self.write_cmd(0x20)
        self.write_cmd(0x11)
        time.sleep_ms(180)
        self.write_cmd(0x29)
        time.sleep_ms(50)

    def show(self):
        # Portrait 128x160 in the 132x162 RAM: col offset=2, row offset=1.
        self.write_cmd(0x2A)   # CASET: columns 2-129  (128 columns)
        self.write_data(0x00)
        self.write_data(0x02)
        self.write_data(0x00)
        self.write_data(0x81)

        self.write_cmd(0x2B)   # RASET: rows 1-160  (160 rows)
        self.write_data(0x00)
        self.write_data(0x01)
        self.write_data(0x00)
        self.write_data(0xA0)

        self.write_cmd(0x2C)

        # MicroPython framebuf stores RGB565 little-endian [lo, hi].
        # ST7735 expects high byte first, so swap each pair before write.
        b = self.buffer
        for i in range(0, len(b), 2):
            b[i], b[i + 1] = b[i + 1], b[i]
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(b)
        self.cs(1)
        # Swap back so framebuf drawing calls remain valid.
        for i in range(0, len(b), 2):
            b[i], b[i + 1] = b[i + 1], b[i]
