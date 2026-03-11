# MIT License
#
# Copyright (c) 2021 Christopher Wells
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from machine import Pin, PWM
import time
import os

import bmp_file_reader as bmpr
import lcd

BL = 13
IMAGE_SECONDS = 5
USE_GIST_COLOR_PACKING = False


def to_color(red, green, blue):
    if USE_GIST_COLOR_PACKING:
        brightness = 1.0

        # Original packing from the referenced gist.
        b = int((blue / 255.0) * (2 ** 5 - 1) * brightness)
        r = int((red / 255.0) * (2 ** 5 - 1) * brightness)
        g = int((green / 255.0) * (2 ** 6 - 1) * brightness)

        bs = b << 8
        rs = r << 3

        g_high = g >> 3
        g_low = (g & 0b000111) << 13
        gs = g_high + g_low

        return bs + rs + gs

    # Standard RGB565 for Waveshare framebuf drivers.
    return ((red & 0xF8) << 8) | ((green & 0xFC) << 3) | (blue >> 3)


def read_bmp_to_buffer(lcd_display, file_handle):
    reader = bmpr.BMPFileReader(file_handle)

    width = min(reader.get_width(), lcd_display.width)
    height = min(reader.get_height(), lcd_display.height)

    x_off = (lcd_display.width - width) // 2
    y_off = (lcd_display.height - height) // 2

    for row_i in range(height):
        row = reader.get_row(row_i)
        for col_i, color in enumerate(row[:width]):
            lcd_display.pixel(
                col_i + x_off,
                row_i + y_off,
                to_color(color.red, color.green, color.blue),
            )


def _find_images_dir():
    if "images" in os.listdir("/"):
        return "/images"
    if "images" in os.listdir("."):
        return "images"
    return None


def main():
    pwm = PWM(Pin(BL))
    pwm.freq(1000)
    pwm.duty_u16(32768)

    lcd_display = lcd.LCD_1inch8()

    lcd_display.fill(lcd_display.WHITE)
    lcd_display.text("Loading...", 2, 28, lcd_display.BLACK)
    lcd_display.show()

    images_dir = _find_images_dir()
    if images_dir is None:
        lcd_display.fill(lcd_display.BLACK)
        lcd_display.text("No /images dir", 2, 28, lcd_display.WHITE)
        lcd_display.show()
        print("No images directory found")
        return

    while True:
        image_names = [n for n in os.listdir(images_dir) if n.lower().endswith(".bmp")]
        image_names.sort()

        if not image_names:
            lcd_display.fill(lcd_display.BLACK)
            lcd_display.text("No BMP files", 2, 20, lcd_display.WHITE)
            lcd_display.text("in /images", 2, 36, lcd_display.WHITE)
            lcd_display.show()
            print("No BMP files found in {}".format(images_dir))
            time.sleep(2)
            continue

        for image_filename in image_names:
            image_path = "{}/{}".format(images_dir, image_filename)
            try:
                lcd_display.fill(lcd_display.BLACK)
                with open(image_path, "rb") as input_stream:
                    read_bmp_to_buffer(lcd_display, input_stream)
                lcd_display.show()
                print("Displayed {}".format(image_path))
            except Exception as exc:
                lcd_display.fill(lcd_display.BLACK)
                lcd_display.text("BMP error", 2, 20, lcd_display.WHITE)
                lcd_display.text(image_filename[:16], 2, 36, lcd_display.WHITE)
                lcd_display.show()
                print("Failed {}: {}".format(image_path, exc))

            time.sleep(IMAGE_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Slideshow stopped")
