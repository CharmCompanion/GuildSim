"""Shared text UI theme helpers for shell first, OLED later."""

try:
    import os
except Exception:  # MicroPython-safe fallback
    os = None


ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_BG_BLACK = "\033[40m"
ANSI_GOLD = "\033[38;5;220m"
ANSI_TAN = "\033[38;5;180m"
ANSI_BROWN = "\033[38;5;130m"
ANSI_ACCENT = "\033[38;5;223m"


def _supports_ansi():
    if os is None:
        return False
    try:
        term = os.getenv("TERM", "")
        no_color = os.getenv("NO_COLOR", "")
        if no_color:
            return False
        if getattr(os, "name", "") == "nt":
            return True
        return bool(term) and term.lower() != "dumb"
    except Exception:
        return False


def _tone(text, fg="", bg="", bold=False):
    if not _supports_ansi():
        return str(text)
    parts = []
    if bold:
        parts.append(ANSI_BOLD)
    if bg:
        parts.append(bg)
    if fg:
        parts.append(fg)
    parts.append(str(text))
    parts.append(ANSI_RESET)
    return "".join(parts)


def _term_width(default=70):
    if os is None:
        return default
    try:
        cols = os.get_terminal_size().columns
        if cols < 40:
            return 40
        if cols > 110:
            return 110
        return cols
    except Exception:
        return default


def _line(width=70, char="="):
    return char * width


def clear_pad(lines=3):
    print("\n" * lines)


def header(title, width=70):
    width = width or _term_width()
    print(_tone(_line(width, "="), fg=ANSI_GOLD, bg=ANSI_BG_BLACK, bold=True))
    print(_tone(str(title).center(width), fg=ANSI_ACCENT, bg=ANSI_BG_BLACK, bold=True))
    print(_tone(_line(width, "="), fg=ANSI_GOLD, bg=ANSI_BG_BLACK, bold=True))


def section(title, width=70):
    width = width or _term_width()
    print(_tone(_line(width, "-"), fg=ANSI_TAN, bg=ANSI_BG_BLACK))
    print(_tone(str(title), fg=ANSI_TAN, bg=ANSI_BG_BLACK, bold=True))
    print(_tone(_line(width, "-"), fg=ANSI_TAN, bg=ANSI_BG_BLACK))


def kv(left, right):
    left_text = _tone(str(left), fg=ANSI_BROWN, bg=ANSI_BG_BLACK, bold=True)
    right_text = _tone(str(right), fg=ANSI_ACCENT, bg=ANSI_BG_BLACK)
    print("{}: {}".format(left_text, right_text))


def bullet(text):
    print(_tone("- {}".format(text), fg=ANSI_TAN, bg=ANSI_BG_BLACK))


def panel(title, rows, width=70):
    width = width or _term_width()
    header(title, width=width)
    for row in rows:
        if isinstance(row, tuple) and len(row) == 2:
            kv(row[0], row[1])
        else:
            print(_tone(str(row), fg=ANSI_ACCENT, bg=ANSI_BG_BLACK))
    print(_tone(_line(width, "="), fg=ANSI_GOLD, bg=ANSI_BG_BLACK, bold=True))


def render_menu(title, items, selected_index):
    width = _term_width(70)
    clear_pad(3)
    header(title, width=width)
    print(_tone("Controls: W (Up), S (Down), Enter (Select), Q (Back/Exit)", fg=ANSI_TAN, bg=ANSI_BG_BLACK))
    print(_tone(_line(width, "-"), fg=ANSI_TAN, bg=ANSI_BG_BLACK))
    for i, item in enumerate(items):
        label = str(item)
        cursor = ">>> " if i == selected_index else "    "
        if i == selected_index:
            line = _tone(cursor + label, fg=ANSI_GOLD, bg=ANSI_BG_BLACK, bold=True)
        else:
            line = _tone(cursor + label, fg=ANSI_ACCENT, bg=ANSI_BG_BLACK)
        print(line)
    print(_tone(_line(width, "="), fg=ANSI_GOLD, bg=ANSI_BG_BLACK, bold=True))


def render(title, rows, mode="shell", oled_callback=None):
    """Render to shell or to an OLED two-line callback."""
    if mode == "oled" and oled_callback:
        for row in rows:
            if isinstance(row, tuple) and len(row) == 2:
                left = str(row[0])
                right = str(row[1])
                oled_callback(left[:16], right[:16])
            else:
                text = str(row)
                oled_callback(str(title)[:16], text[:16])
        return

    panel(title, rows)
