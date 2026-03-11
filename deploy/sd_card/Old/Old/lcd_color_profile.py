"""Panel color profile for Pico ST7735 display."""


def rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


# Calibrated from on-device sweep: MODE 1 was closest.
ACTIVE_MODE = 1


def map_rgb(r, g, b, mode=ACTIVE_MODE):
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
