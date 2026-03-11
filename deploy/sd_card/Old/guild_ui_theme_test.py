from machine import Pin, PWM
import lcd

# Toggle if your panel path still has red/blue swapped.
SWAP_RB = False


def color565(r, g, b):
    if SWAP_RB:
        r, b = b, r
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def draw_guild_ui(display):
    # Fantasy palette from user picks.
    # Parchment: #F5DEB3 (Wheat)
    parchment = color565(245, 222, 179)
    # Alternate parchment: #DEB887 (BurlyWood)
    parchment_alt = color565(222, 184, 135)
    # Deep brown text/border: #5D4037
    deep_brown = color565(93, 64, 55)
    # Gold accents: #FFD700
    gold = color565(255, 215, 0)
    shadow_brown = color565(60, 40, 34)

    w = display.width
    h = display.height

    # Book cover base.
    display.fill(deep_brown)

    # Parchment page inset.
    margin = 8
    page_w = w - (margin * 2)
    page_h = h - (margin * 2)
    display.fill_rect(margin, margin, page_w, page_h, parchment)

    # Subtle parchment tint strip for a paper-like feel.
    display.fill_rect(margin, margin + page_h - 18, page_w, 18, parchment_alt)

    # Deep brown frame with inner gold line.
    display.rect(margin + 1, margin + 1, page_w - 2, page_h - 2, deep_brown)
    display.rect(margin + 2, margin + 2, page_w - 4, page_h - 4, deep_brown)
    display.rect(margin + 4, margin + 4, page_w - 8, page_h - 8, gold)

    # Title and separators with one-pixel shadow.
    display.text("GUILD SIM", 47, 19, shadow_brown)
    display.text("GUILD SIM", 46, 18, deep_brown)
    display.hline(20, 34, w - 40, gold)

    # Menu items with gold selector indicators.
    display.text(">", 22, 52, gold)
    display.text("ROSTER", 34, 52, deep_brown)
    display.text(">", 22, 72, gold)
    display.text("MISSIONS", 34, 72, deep_brown)
    display.text(">", 22, 92, gold)
    display.text("UPGRADES", 34, 92, deep_brown)

    # Footer accent + tiny palette verification swatches.
    display.fill_rect(20, h - 22, w - 40, 2, gold)
    display.fill_rect(24, h - 14, 12, 8, parchment)
    display.fill_rect(40, h - 14, 12, 8, deep_brown)
    display.fill_rect(56, h - 14, 12, 8, gold)


def main():
    bl = PWM(Pin(13))
    bl.freq(1000)
    bl.duty_u16(52000)

    display = lcd.LCD_1inch8()
    draw_guild_ui(display)
    display.show()
    print("Guild Sim UI Loaded")


if __name__ == "__main__":
    main()
