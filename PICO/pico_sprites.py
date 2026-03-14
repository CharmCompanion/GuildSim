from pico_assets import draw_recruit_asset


def _rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def _hash_id(text):
    h = 2166136261
    for ch in text:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def _palette_for_recruit(recruit):
    h = _hash_id(recruit.get("id", recruit.get("name", "r")))
    skin = [
        _rgb565(245, 214, 189),
        _rgb565(219, 173, 130),
        _rgb565(179, 124, 87),
        _rgb565(125, 86, 63),
    ][h % 4]
    hair = [
        _rgb565(45, 34, 30),
        _rgb565(96, 58, 40),
        _rgb565(170, 123, 70),
        _rgb565(218, 197, 116),
        _rgb565(121, 58, 143),
        _rgb565(52, 98, 162),
    ][(h >> 5) % 6]
    cloth = [
        _rgb565(68, 109, 173),
        _rgb565(120, 66, 45),
        _rgb565(54, 127, 70),
        _rgb565(126, 66, 132),
        _rgb565(145, 112, 44),
    ][(h >> 9) % 5]
    return skin, hair, cloth


def draw_recruit(display, x, y, recruit, scale=1):
    """Draw a deterministic 12x16 mini-sprite based on recruit id."""
    if scale == 1 and draw_recruit_asset(display, recruit, x, y):
        return

    skin, hair, cloth = _palette_for_recruit(recruit)
    black = _rgb565(0, 0, 0)

    w = 12 * scale
    h = 16 * scale

    # Outline body box
    display.rect(x, y, w, h, black)

    # Head
    display.fill_rect(x + 3 * scale, y + 1 * scale, 6 * scale, 4 * scale, skin)
    # Hair band
    display.fill_rect(x + 3 * scale, y + 1 * scale, 6 * scale, 1 * scale, hair)

    # Torso
    display.fill_rect(x + 2 * scale, y + 5 * scale, 8 * scale, 6 * scale, cloth)
    # Arms
    display.fill_rect(x + 1 * scale, y + 6 * scale, 1 * scale, 4 * scale, skin)
    display.fill_rect(x + 10 * scale, y + 6 * scale, 1 * scale, 4 * scale, skin)

    # Legs
    display.fill_rect(x + 3 * scale, y + 11 * scale, 2 * scale, 4 * scale, cloth)
    display.fill_rect(x + 7 * scale, y + 11 * scale, 2 * scale, 4 * scale, cloth)

    # Role mark
    jc = recruit.get("job_class", "Recruit")
    if jc in ("Mage", "Necromancer"):
        display.pixel(x + 6 * scale, y + 8 * scale, _rgb565(90, 200, 255))
    elif jc in ("Warrior", "Knight", "Paladin"):
        display.pixel(x + 6 * scale, y + 8 * scale, _rgb565(220, 80, 80))
    elif jc in ("Ranger", "Assassin"):
        display.pixel(x + 6 * scale, y + 8 * scale, _rgb565(100, 220, 120))
