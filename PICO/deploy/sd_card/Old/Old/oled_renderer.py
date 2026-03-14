"""Optional OLED renderer adapter using encoder_menu.display(text1, text2)."""


def render_two_line(title, body, display_func=None):
    if display_func is None:
        try:
            from encoder_menu import display as display_func  # pyright: ignore[reportMissingImports]
        except Exception:
            display_func = None

    if not display_func:
        print(title)
        print(body)
        return False

    display_func(str(title)[:16], str(body)[:16])
    return True
