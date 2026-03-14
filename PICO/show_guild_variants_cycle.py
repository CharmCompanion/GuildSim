from machine import Pin, PWM  # pyright: ignore[reportMissingImports]
import time

import lcd
from bmp24_stream import BMP24Reader


IMAGES = [
    "/images/guild_test_fit_1_1.bmp",
]


def color565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def draw_bmp(display, path):
    with open(path, "rb") as f:
        reader = BMP24Reader(f)
        w = min(reader.width, display.width)
        h = min(reader.height, display.height)
        x_off = (display.width - w) // 2
        y_off = (display.height - h) // 2

        display.fill(0x0000)
        for y in range(h):
            x = x_off
            for r, g, b in reader.iter_pixels(y):
                if x >= x_off + w:
                    break
                display.pixel(x, y + y_off, color565(r, g, b))
                x += 1


def main():
    bl = PWM(Pin(13))
    bl.freq(1000)
    bl.duty_u16(0)

    d = lcd.LCD_1inch8()

    total = len(IMAGES)
    while True:
        for idx, path in enumerate(IMAGES, start=1):
            try:
                draw_bmp(d, path)
                d.show()
                bl.duty_u16(56000)
                print("Displayed", path)
                time.sleep(3)
            except Exception as exc:
                d.fill(0x0000)
                d.text("MISSING", 4, 4, 0xFFFF)
                d.text(str(idx), 4, 18, 0xFFFF)
                d.show()
                print("Failed", path, exc)
                time.sleep(2)


if __name__ == "__main__":
    main()
