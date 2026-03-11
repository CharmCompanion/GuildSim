import sys
import ui_theme


class Menu:
    """Simple terminal menu for PC and Thonny shell testing."""

    def __init__(self, items, title="MENU"):
        self.menu_items = items
        self.selected_index = 0
        self.title = title

    def _label(self, item):
        label = item.get("label", "")
        if callable(label):
            return str(label())
        return str(label)

    def display(self):
        labels = [self._label(item) for item in self.menu_items]
        ui_theme.render_menu(self.title, labels, self.selected_index)

    def move(self, direction):
        self.selected_index = (self.selected_index + direction) % len(self.menu_items)
        self.display()

    def select(self):
        item = self.menu_items[self.selected_index]
        action = item.get("action")
        if callable(action):
            action()


def read_command(prompt="w/s/enter/q > "):
    """Cross-platform blocking command input for Thonny shell workflows."""
    try:
        return input(prompt).strip().lower()
    except (EOFError, KeyboardInterrupt):
        return "q"
