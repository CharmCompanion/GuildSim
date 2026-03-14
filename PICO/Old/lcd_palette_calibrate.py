from machine import Pin, PWM
import time

from st7735_1inch8 import LCD_1inch8


MODE_DELAY_SEC = 3.5
RUN_FOREVER = True


def rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def map_rgb(r, g, b, mode):
    if mode == 0:
        return rgb565(r, g, b)
    if mode == 1:
        return rgb565(r, b, g)
    if mode == 2:
        return rgb565(g, r, b)
    if mode == 3:
        return rgb565(g, b, r)
    if mode == 4:
        return rgb565(b, r, g)
    return rgb565(b, g, r)


def draw_mode(lcd, mode):
    black = map_rgb(0, 0, 0, mode)
    white = map_rgb(255, 255, 255, mode)
    brown = map_rgb(101, 67, 33, mode)
    tan = map_rgb(210, 180, 140, mode)
    gold = map_rgb(212, 175, 55, mode)

    lcd.fill(black)
    lcd.text("MODE {}".format(mode), 8, 8, white)
    lcd.text("BROWN TAN GOLD", 8, 24, white)
    lcd.fill_rect(8, 48, 44, 40, brown)
    lcd.fill_rect(56, 48, 44, 40, tan)
    lcd.fill_rect(104, 48, 44, 40, gold)
    lcd.text("Pick best mode", 8, 100, white)
    lcd.show()


def main():
    bl = PWM(Pin(13))
    bl.freq(1000)
    bl.duty_u16(42000)

    lcd = LCD_1inch8()

    print("Palette calibration start")
    print("Watch screen. Report best MODE number (0..5)")

    while True:
        for mode in range(6):
            print("MODE", mode)
            draw_mode(lcd, mode)
            time.sleep(MODE_DELAY_SEC)

        if not RUN_FOREVER:
            break

    print("Palette calibration done")


if __name__ == "__main__":
    main()
