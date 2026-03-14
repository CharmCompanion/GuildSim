from machine import Pin, PWM  # pyright: ignore[reportMissingImports]
import time
import lcd  # pyright: ignore[reportMissingImports]


SECONDS_PER_MODE = 2.5

# 0: rgb, 1: rbg, 2: grb, 3: gbr, 4: brg, 5: bgr
MODES = (0, 1, 2, 3, 4, 5)


def map_rgb565(r, g, b, mode):
    if mode == 0:
        rr, gg, bb = r, g, b
    elif mode == 1:
        rr, gg, bb = r, b, g
    elif mode == 2:
        rr, gg, bb = g, r, b
    elif mode == 3:
        rr, gg, bb = g, b, r
    elif mode == 4:
        rr, gg, bb = b, r, g
    else:
        rr, gg, bb = b, g, r
    return ((rr & 0xF8) << 8) | ((gg & 0xFC) << 3) | (bb >> 3)


def draw_bars(d, mode):
    bars = [
        (255, 0, 0, "R"),
        (0, 255, 0, "G"),
        (0, 0, 255, "B"),
        (255, 255, 0, "Y"),
        (0, 255, 255, "C"),
        (255, 0, 255, "M"),
        (255, 255, 255, "W"),
        (0, 0, 0, "K"),
    ]

    w = 20
    d.fill(0x0000)
    for i, (r, g, b, label) in enumerate(bars):
        x = i * w
        color = map_rgb565(r, g, b, mode)
        d.fill_rect(x, 14, w, 114, color)
        text_color = 0x0000 if (r + g + b) > 500 else 0xFFFF
        d.text(label, x + 6, 60, text_color)

    d.fill_rect(0, 0, 160, 12, 0x0000)
    d.text("RAINBOW MODE {}".format(mode), 2, 2, 0xFFFF)



def main():
    bl = PWM(Pin(13))
    bl.freq(1000)
    bl.duty_u16(36000)

    d = lcd.LCD_1inch8()

    print("Rainbow calibration start")
    print("Pick MODE where bars look true: R G B Y C M W K")

    while True:
        for mode in MODES:
            draw_bars(d, mode)
            d.show()
            print("MODE", mode)
            time.sleep(SECONDS_PER_MODE)


if __name__ == "__main__":
    main()
