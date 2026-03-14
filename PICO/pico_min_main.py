from machine import Pin, PWM  # pyright: ignore[reportMissingImports]
import time

import lcd


def main():
    bl = PWM(Pin(13))
    bl.freq(1000)
    bl.duty_u16(65535)

    d = lcd.LCD_1inch8()

    colors = (
        (0xF800, "RED"),
        (0x07E0, "GREEN"),
        (0x001F, "BLUE"),
        (0xFFFF, "WHITE"),
        (0x0000, "BLACK"),
    )

    while True:
        for c, name in colors:
            d.fill(c)
            text_color = 0x0000 if c == 0xFFFF else 0xFFFF
            d.text("PICO LCD TEST", 14, 68, text_color)
            d.text(name, 50, 84, text_color)
            d.show()
            time.sleep_ms(700)


if __name__ == "__main__":
    main()
