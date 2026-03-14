from machine import Pin, PWM
from st7735_1inch8 import LCD_1inch8


def rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def main():
    bl = PWM(Pin(13))
    bl.freq(1000)
    bl.duty_u16(54000)

    lcd = LCD_1inch8()
    w = lcd.width
    h = lcd.height

    # Full-screen horizontal rainbow only.
    for y in range(h):
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

    lcd.show()
    print("Rainbow-only frame rendered")


if __name__ == "__main__":
    main()
