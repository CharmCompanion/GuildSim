from machine import Pin, PWM  # pyright: ignore[reportMissingImports]
import lcd  # pyright: ignore[reportMissingImports]


def panel565(r, g, b):
    # Current panel profile: G/B swapped path in this project.
    return ((r & 0xF8) << 8) | ((b & 0xFC) << 3) | (g >> 3)


def draw_ramps(d):
    w = d.width
    h = d.height
    band = h // 3

    for x in range(w):
        t = int((x * 255) / max(1, w - 1))
        # Top band: Red ramp
        c_r = panel565(t, 0, 0)
        # Middle band: Green ramp
        c_g = panel565(0, t, 0)
        # Bottom band: Blue ramp
        c_b = panel565(0, 0, t)

        d.vline(x, 0, band, c_r)
        d.vline(x, band, band, c_g)
        d.vline(x, band * 2, h - band * 2, c_b)

    # Reference patches on right edge.
    x0 = w - 24
    d.fill_rect(x0, 4, 20, 10, panel565(255, 255, 255))   # white
    d.fill_rect(x0, 18, 20, 10, panel565(128, 128, 128))  # gray
    d.fill_rect(x0, 32, 20, 10, panel565(255, 128, 128))  # salmon
    d.fill_rect(x0, 46, 20, 10, panel565(128, 64, 32))    # brown

    # Labels
    d.fill_rect(0, 0, 58, 36, panel565(0, 0, 0))
    d.text("R", 2, 4, panel565(255, 255, 255))
    d.text("G", 2, band + 4, panel565(255, 255, 255))
    d.text("B", 2, band * 2 + 4, panel565(255, 255, 255))


def main():
    bl = PWM(Pin(13))
    bl.freq(1000)
    bl.duty_u16(36000)

    d = lcd.LCD_1inch8()
    d.fill(panel565(0, 0, 0))
    draw_ramps(d)
    d.show()
    print("CHANNEL_RAMP_DONE")


if __name__ == "__main__":
    main()
