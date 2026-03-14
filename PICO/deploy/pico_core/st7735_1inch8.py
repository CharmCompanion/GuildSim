from machine import Pin, SPI
import framebuf
import time


# ST7735 panel fix: keep BGR color order, inversion OFF.
DEFAULT_MADCTL = 0x78
DEFAULT_INVERSION_ON = False


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
        self.width = 160
        self.height = 128

        self.cs = Pin(9, Pin.OUT)
        self.rst = Pin(12, Pin.OUT)
        self.dc = Pin(8, Pin.OUT)

        # Optional touch CS pin on some boards.
        self.tp_cs = Pin(7, Pin.OUT)
        self.tp_cs.value(1)

        self.spi = SPI(
            1,
            # Minimum practical rate to diagnose severe signal-integrity issues.
            baudrate=125_000,
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
        # MADCTL controls color order/scan direction. This value is panel-specific.
        self.write_data(DEFAULT_MADCTL)

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

        if DEFAULT_INVERSION_ON:
            self.write_cmd(0x21)
        else:
            self.write_cmd(0x20)
        self.write_cmd(0x11)
        time.sleep_ms(180)
        self.write_cmd(0x29)
        time.sleep_ms(50)

    def show(self):
        # Common offsets for 128x160 panel in 132x162 RAM.
        self.write_cmd(0x2A)
        self.write_data(0x00)
        self.write_data(0x01)
        self.write_data(0x00)
        self.write_data(0xA0)

        self.write_cmd(0x2B)
        self.write_data(0x00)
        self.write_data(0x02)
        self.write_data(0x00)
        self.write_data(0x81)

        self.write_cmd(0x2C)

        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(self.buffer)
        self.cs(1)
