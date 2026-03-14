from machine import Pin, PWM  # pyright: ignore[reportMissingImports]
import lcd  # pyright: ignore[reportMissingImports]


def panel565(r, g, b):
    # Encode as R,B,G for this panel's G/B swap behavior.
    # Blue correction reduces violet cast on this panel.
    rr, gg, bb = r, g, b
    if bb > 160 and rr < 100 and gg < 140:
        rr = 0 if rr < 12 else rr - 12
        gg = 255 if gg > 243 else gg + 12
    return ((rr & 0xF8) << 8) | ((bb & 0xFC) << 3) | (gg >> 3)


def main():
    bl = PWM(Pin(13))
    bl.freq(1000)
    bl.duty_u16(36000)

    d = lcd.LCD_1inch8()
    d.fill(0x0000)

    # Static, no animation: best for detecting pure signal noise.
    d.fill_rect(0, 0, 80, 64, panel565(255, 0, 0))       # red
    d.fill_rect(80, 0, 80, 64, panel565(0, 255, 0))      # green
    d.fill_rect(0, 64, 80, 64, panel565(0, 0, 255))      # blue
    d.fill_rect(80, 64, 80, 64, panel565(255, 255, 255)) # white

    d.rect(0, 0, 160, 128, 0xFFFF)
    d.text("STATIC TEST", 28, 54, 0x0000)
    d.show()
    print("STATIC_BLOCKS_DONE")


if __name__ == "__main__":
    main()
