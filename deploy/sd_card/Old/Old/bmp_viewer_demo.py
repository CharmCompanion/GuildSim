"""Display 24-bit BMP images from /images on Waveshare Pico LCD 1.8.

Expected on Pico filesystem:
- /st7735_1inch8.py
- /bmp24_stream.py
- /images/*.bmp
"""

import os
import time
from machine import Pin, PWM

from st7735_1inch8 import LCD_1inch8
from bmp24_stream import BMP24Reader, rgb565, bgr565


# Set to True if reds/blues appear swapped on your panel path.
USE_BGR565 = False
DISPLAY_SECONDS = 3


def _color565(r, g, b):
    return bgr565(r, g, b) if USE_BGR565 else rgb565(r, g, b)


def draw_bmp_to_lcd(lcd, bmp_path):
    with open(bmp_path, "rb") as f:
        reader = BMP24Reader(f)

        if reader.width > lcd.width or reader.height > lcd.height:
            raise ValueError("Image too large for LCD: {}x{}".format(reader.width, reader.height))

        lcd.fill(0x0000)

        # Center image on the 160x128 buffer.
        x_off = (lcd.width - reader.width) // 2
        y_off = (lcd.height - reader.height) // 2

        for y in range(reader.height):
            yy = y + y_off
            if yy < 0 or yy >= lcd.height:
                continue
            x = x_off
            for r, g, b in reader.iter_pixels(y):
                if 0 <= x < lcd.width:
                    lcd.pixel(x, yy, _color565(r, g, b))
                x += 1

        lcd.show()


def main():
    bl = PWM(Pin(13))
    bl.freq(1000)
    bl.duty_u16(52000)

    lcd = LCD_1inch8()
    lcd.fill(0x0000)
    lcd.text("BMP viewer booting", 8, 8, 0xFFFF)
    lcd.show()

    image_dir = "images"
    if image_dir not in os.listdir("/") and image_dir not in os.listdir("."):
        lcd.fill(0x0000)
        lcd.text("No /images folder", 8, 8, 0xFFFF)
        lcd.text("Add 24-bit .bmp", 8, 24, 0xFFFF)
        lcd.show()
        print("No /images folder found")
        return

    if image_dir in os.listdir("/"):
        base = "/images"
    else:
        base = "images"

    files = [name for name in os.listdir(base) if name.lower().endswith(".bmp")]
    files.sort()

    if not files:
        lcd.fill(0x0000)
        lcd.text("No BMP files", 8, 8, 0xFFFF)
        lcd.text("in /images", 8, 24, 0xFFFF)
        lcd.show()
        print("No .bmp files in {}".format(base))
        return

    print("Found {} BMP files".format(len(files)))
    while True:
        for filename in files:
            path = "{}/{}".format(base, filename)
            try:
                print("Displaying {}".format(path))
                draw_bmp_to_lcd(lcd, path)
            except Exception as exc:
                lcd.fill(0x0000)
                lcd.text("BMP error", 8, 8, 0xFFFF)
                lcd.text(filename[:18], 8, 24, 0xFFFF)
                lcd.show()
                print("Failed {}: {}".format(path, exc))
            time.sleep(DISPLAY_SECONDS)


if __name__ == "__main__":
    main()
