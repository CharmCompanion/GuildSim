from machine import Pin, PWM  # pyright: ignore[reportMissingImports]
import time
import lcd


def main():
    bl = PWM(Pin(13))
    bl.freq(1000)
    bl.duty_u16(52000)

    d = lcd.LCD_1inch8()

    colors = [
        (0xF800, "RED"),
        (0x07E0, "GREEN"),
        (0x001F, "BLUE"),
        (0xFFFF, "WHITE"),
        (0x0000, "BLACK"),
    ]

    while True:
        for color, name in colors:
            d.fill(color)
            text_color = 0x0000 if color == 0xFFFF else 0xFFFF
            d.text("SCREEN DIAG", 20, 54, text_color)
            d.text(name, 48, 72, text_color)
            d.text("GP8-13", 44, 90, text_color)
            d.show()
            time.sleep(1)


if __name__ == "__main__":
    main()
