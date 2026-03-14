from machine import Pin, PWM  # pyright: ignore[reportMissingImports]
import time
import lcd  # pyright: ignore[reportMissingImports]
from bmp24_stream import BMP24Reader


IMAGE_PATH = "chopper_160x128.bmp"
SECONDS_PER_PROFILE = 2.2

# mode mapping from old calibration work.
# 0: rgb, 1: rbg, 2: grb, 3: gbr, 4: brg, 5: bgr
MODES = (0, 1, 2, 3, 4, 5)

# Common ST7735 MADCTL values seen across this project history.
MADCTLS = (0x70, 0xC8, 0x00, 0x08)
INVERSION = (False, True)


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


def set_panel_profile(d, madctl, invert):
    d.write_cmd(0x36)
    d.write_data(madctl)
    d.write_cmd(0x21 if invert else 0x20)


def draw_bmp(display, path, mode):
    with open(path, "rb") as f:
        reader = BMP24Reader(f)
        w = min(reader.width, display.width)
        h = min(reader.height, display.height)
        x_off = (display.width - w) // 2
        y_off = (display.height - h) // 2

        display.fill(0x0000)
        for y in range(h):
            x = x_off
            for r, g, b in reader.iter_pixels(y):
                if x >= x_off + w:
                    break
                display.pixel(x, y + y_off, map_rgb565(r, g, b, mode))
                x += 1


def draw_label(display, text):
    display.fill_rect(0, 0, 160, 12, 0x0000)
    display.text(text[:24], 2, 2, 0xFFFF)


def main():
    bl = PWM(Pin(13))
    bl.freq(1000)
    bl.duty_u16(56000)

    d = lcd.LCD_1inch8()

    profiles = []
    for madctl in MADCTLS:
        for invert in INVERSION:
            for mode in MODES:
                profiles.append((madctl, invert, mode))

    print("Tuning start")
    print("Watch screen and note best profile text")

    while True:
        for madctl, invert, mode in profiles:
            set_panel_profile(d, madctl, invert)
            draw_bmp(d, IMAGE_PATH, mode)
            tag = "M{:02X} I{} C{}".format(madctl, 1 if invert else 0, mode)
            draw_label(d, tag)
            d.show()
            print("PROFILE", tag)
            time.sleep(SECONDS_PER_PROFILE)


if __name__ == "__main__":
    main()
