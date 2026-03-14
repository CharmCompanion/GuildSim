from machine import Pin, PWM  # pyright: ignore[reportMissingImports]
import time
import lcd  # pyright: ignore[reportMissingImports]


# Try common ST7735 variants quickly.
PROFILES = (
    ("M70 I0", 0x70, False),
    ("M78 I0", 0x78, False),
    ("MC8 I0", 0xC8, False),
    ("M78 I1", 0x78, True),
)
SECONDS_PER_PROFILE = 2.5


def rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def hsv_to_rgb(h, s, v):
    # h in [0,1), s,v in [0,1]
    i = int(h * 6.0)
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - f * s)
    t = v * (1.0 - (1.0 - f) * s)
    i %= 6

    if i == 0:
        r, g, b = v, t, p
    elif i == 1:
        r, g, b = q, v, p
    elif i == 2:
        r, g, b = p, v, t
    elif i == 3:
        r, g, b = p, q, v
    elif i == 4:
        r, g, b = t, p, v
    else:
        r, g, b = v, p, q

    return int(r * 255), int(g * 255), int(b * 255)


def set_profile(d, madctl, invert):
    d.write_cmd(0x36)
    d.write_data(madctl)
    d.write_cmd(0x21 if invert else 0x20)


def draw_smooth_gradient(d):
    w = d.width
    h = d.height
    grad_h = h - 18

    # Main smooth HSV field: hue across X, saturation down Y.
    for y in range(grad_h):
        s = y / max(1, grad_h - 1)
        for x in range(w):
            hval = x / max(1, w - 1)
            r, g, b = hsv_to_rgb(hval, s, 1.0)
            d.pixel(x, y, rgb565(r, g, b))

    # Bottom grayscale strip for banding/noise check.
    y0 = grad_h
    for x in range(w):
        c = int((x * 255) / max(1, w - 1))
        col = rgb565(c, c, c)
        d.vline(x, y0, h - y0, col)


def main():
    bl = PWM(Pin(13))
    bl.freq(1000)
    bl.duty_u16(42000)

    d = lcd.LCD_1inch8()

    print("SMOOTH_PROBE_START")
    while True:
        for name, madctl, invert in PROFILES:
            set_profile(d, madctl, invert)
            draw_smooth_gradient(d)
            d.fill_rect(0, 0, d.width, 12, 0x0000)
            d.text(name, 4, 2, 0xFFFF)
            d.show()
            print("PROFILE", name)
            time.sleep(SECONDS_PER_PROFILE)


if __name__ == "__main__":
    main()
