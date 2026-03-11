from machine import Pin, PWM
import lcd


def main():
    bl = PWM(Pin(13))
    bl.freq(1000)
    bl.duty_u16(56000)

    d = lcd.LCD_1inch8()

    d.fill(0x0000)

    # Reference bars: RED, GREEN, BLUE, WHITE, BLACK, GOLD
    bars = [
        ("RED", 0xF800),
        ("GREEN", 0x07E0),
        ("BLUE", 0x001F),
        ("WHITE", 0xFFFF),
        ("BLACK", 0x0000),
        ("GOLD", 0xD5A0),
    ]

    y = 4
    for name, color in bars:
        d.fill_rect(4, y, 90, 18, color)
        d.rect(4, y, 90, 18, 0xFFFF if color == 0x0000 else 0x0000)
        d.text(name, 100, y + 5, 0xFFFF)
        y += 20

    d.show()
    print("Final color test rendered")


if __name__ == "__main__":
    main()
