from machine import Pin, PWM
import time

from st7735_1inch8 import LCD_1inch8


def rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def main():
    bl = PWM(Pin(13))
    bl.freq(1000)
    bl.duty_u16(50000)

    lcd = LCD_1inch8()
    w = lcd.width
    h = lcd.height

    # Horizontal full-spectrum gradient by HSV-like segmentation.
    # Top 96 rows: rainbow sweep.
    for y in range(0, 96):
        for x in range(w):
            t = (x * 6 * 256) // w
            seg = t // 256
            pos = t % 256

            if seg == 0:
                r, g, b = 255, pos, 0
            elif seg == 1:
                r, g, b = 255 - pos, 255, 0
            elif seg == 2:
                r, g, b = 0, 255, pos
            elif seg == 3:
                r, g, b = 0, 255 - pos, 255
            elif seg == 4:
                r, g, b = pos, 0, 255
            else:
                r, g, b = 255, 0, 255 - pos

            lcd.pixel(x, y, rgb565(r, g, b))

    # Middle strip: red, green, blue ramps for channel validation.
    for x in range(w):
        val = (x * 255) // (w - 1)
        lcd.pixel(x, 98, rgb565(val, 0, 0))
        lcd.pixel(x, 99, rgb565(val, 0, 0))
        lcd.pixel(x, 102, rgb565(0, val, 0))
        lcd.pixel(x, 103, rgb565(0, val, 0))
        lcd.pixel(x, 106, rgb565(0, 0, val))
        lcd.pixel(x, 107, rgb565(0, 0, val))

    # Bottom swatches: white, black, gray, yellow, cyan, magenta.
    swatches = [
        rgb565(255, 255, 255),
        rgb565(0, 0, 0),
        rgb565(128, 128, 128),
        rgb565(255, 255, 0),
        rgb565(0, 255, 255),
        rgb565(255, 0, 255),
    ]
    sw_w = w // len(swatches)
    for i, col in enumerate(swatches):
        x0 = i * sw_w
        x1 = w if i == len(swatches) - 1 else (i + 1) * sw_w
        lcd.fill_rect(x0, 112, x1 - x0, 16, col)

    lcd.show()
    print("LCD spectrum test rendered")


if __name__ == "__main__":
    main()
