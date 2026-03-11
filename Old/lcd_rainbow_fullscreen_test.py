from machine import Pin, PWM
import lcd


def wheel(pos):
    # 0-255 color wheel: red -> green -> blue -> red
    if pos < 85:
        return 255 - pos * 3, pos * 3, 0
    if pos < 170:
        pos -= 85
        return 0, 255 - pos * 3, pos * 3
    pos -= 170
    return pos * 3, 0, 255 - pos * 3


def color565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def main():
    bl = PWM(Pin(13))
    bl.freq(1000)
    # Keep backlight dark until first frame is fully pushed.
    bl.duty_u16(0)

    d = lcd.LCD_1inch8()
    w = d.width
    h = d.height

    # Horizontal rainbow sweep plus a slight vertical brightness falloff.
    for y in range(h):
        # Keep enough brightness at bottom to spot line artifacts.
        shade = 255 - ((y * 70) // max(1, h - 1))
        for x in range(w):
            p = (x * 255) // max(1, w - 1)
            r, g, b = wheel(p)
            r = (r * shade) // 255
            g = (g * shade) // 255
            b = (b * shade) // 255
            d.pixel(x, y, color565(r, g, b))

    # Bottom reference strip: pure RGB + white + black blocks.
    bar_h = 10
    y0 = h - bar_h
    seg = w // 5
    d.fill_rect(0, y0, seg, bar_h, color565(255, 0, 0))
    d.fill_rect(seg, y0, seg, bar_h, color565(0, 255, 0))
    d.fill_rect(seg * 2, y0, seg, bar_h, color565(0, 0, 255))
    d.fill_rect(seg * 3, y0, seg, bar_h, color565(255, 255, 255))
    d.fill_rect(seg * 4, y0, w - seg * 4, bar_h, color565(0, 0, 0))

    d.show()
    bl.duty_u16(56000)
    print("Fullscreen rainbow test rendered")


if __name__ == "__main__":
    main()
