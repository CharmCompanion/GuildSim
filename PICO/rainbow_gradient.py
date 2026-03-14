from machine import Pin, PWM  # pyright: ignore[reportMissingImports]
import lcd  # pyright: ignore[reportMissingImports]


def rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def rainbow_color(x, width):
    # 6-segment rainbow across screen width.
    p = (x * 1535) // max(1, width - 1)
    seg = p // 256
    t = p % 256

    if seg == 0:    # red -> yellow
        return 255, t, 0
    if seg == 1:    # yellow -> green
        return 255 - t, 255, 0
    if seg == 2:    # green -> cyan
        return 0, 255, t
    if seg == 3:    # cyan -> blue
        return 0, 255 - t, 255
    if seg == 4:    # blue -> magenta
        return t, 0, 255
    return 255, 0, 255 - t  # magenta -> red


def main():
    bl = PWM(Pin(13))
    bl.freq(1000)
    bl.duty_u16(42000)

    d = lcd.LCD_1inch8()
    w = d.width
    h = d.height

    for x in range(w):
        r, g, b = rainbow_color(x, w)
        c = rgb565(r, g, b)
        d.vline(x, 0, h, c)

    d.fill_rect(0, 0, w, 12, 0x0000)
    d.text("RAINBOW GRADIENT", 8, 2, 0xFFFF)
    d.show()
    print("RAINBOW_DONE")


if __name__ == "__main__":
    main()
