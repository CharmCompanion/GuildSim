from machine import Pin, PWM
import time
import lcd


# Buttons (wire to GND for press).
BTN_DOWN_PIN = 14
BTN_SELECT_PIN = 15
BTN_BACK_PIN = 16


class DebouncedButton:
    def __init__(self, pin, debounce_ms=8, cooldown_ms=0):
        self.pin = pin
        self.debounce_ms = debounce_ms
        self.cooldown_ms = cooldown_ms
        self.raw_state = self.pin.value() == 0
        self.stable_state = self.raw_state
        self.last_change_ms = time.ticks_ms()
        self.last_press_ms = time.ticks_ms()

    def update(self):
        now = time.ticks_ms()
        raw = self.pin.value() == 0

        if raw != self.raw_state:
            self.raw_state = raw
            self.last_change_ms = now

        pressed_event = False
        if time.ticks_diff(now, self.last_change_ms) >= self.debounce_ms:
            if self.stable_state != self.raw_state:
                self.stable_state = self.raw_state
                if self.stable_state and time.ticks_diff(now, self.last_press_ms) >= self.cooldown_ms:
                    self.last_press_ms = now
                    pressed_event = True

        return self.stable_state, pressed_event

# Fantasy Book palette (RGB565) provided by user.
COL_PARCHMENT = 0xF792
COL_INK = 0x3944
COL_GOLD = 0xFEA0
COL_COPPER = 0xC4A5
COL_BLACK = 0x0000

# 8x8 font means max ~20 chars on 160px width.
MAX_CHARS = 20

TOWNS = [
    "IRONHOLD",
    "DUSKVEIL",
    "FROSTGATE",
    "EMBERFALL",
    "THORNHAVEN",
    "RAVENMARCH",
    "STONEKEEP",
    "AETHERFORD",
]

PAGES = ["HOME", "TOWN", "BUILD", "LOG"]


class Game:
    def __init__(self):
        self.town_index = 0
        self.page_index = 0

        self.day = 1
        self.gold = 220
        self.wood = 50
        self.stone = 35
        self.relics = 0

        self.population = 20
        self.happiness = 75

        self.houses = 2
        self.farms = 1
        self.market = 1
        self.guild = 1

        self.log = "Chronicle begun"

    @property
    def town(self):
        return TOWNS[self.town_index]

    @property
    def page(self):
        return PAGES[self.page_index]

    def next_page(self):
        self.page_index = (self.page_index + 1) % len(PAGES)

    def prev_page(self):
        self.page_index = (self.page_index - 1) % len(PAGES)

    def next_town(self):
        self.town_index = (self.town_index + 1) % len(TOWNS)

    def tick_day(self):
        self.day += 1

        # Economy loop.
        self.gold += self.market * 4 + self.population // 6
        self.wood += self.farms * 2
        self.stone += max(1, self.houses // 2)

        # Upkeep.
        self.gold = max(0, self.gold - (self.houses + self.market))

        # Event roll.
        roll = time.ticks_cpu() & 0xFF
        if roll < 40:
            gain = 2 + (roll % 6)
            self.gold += gain
            self.log = "+{}g caravan".format(gain)
        elif roll < 76:
            gain = 1 + (roll % 2)
            self.relics += gain
            self.log = "+{} relic".format(gain)
        elif roll < 112:
            loss = 2 + (roll % 4)
            self.gold = max(0, self.gold - loss)
            self.happiness = max(35, self.happiness - 2)
            self.log = "bandits -{}g".format(loss)
        elif roll < 146:
            self.happiness = min(99, self.happiness + 2)
            self.log = "festival mood up"

        # Growth/decline pressure.
        if self.happiness >= 80 and (self.day % 3) == 0:
            self.population += 1
        elif self.happiness <= 45 and self.population > 8 and (self.day % 4) == 0:
            self.population -= 1

    def try_build(self):
        # Keep mechanics simple and readable for v-pet flow.
        if self.gold >= 60 and self.wood >= 20:
            self.gold -= 60
            self.wood -= 20
            self.houses += 1
            self.log = "houses x{}".format(self.houses)
            return

        if self.gold >= 80 and self.stone >= 18:
            self.gold -= 80
            self.stone -= 18
            self.market += 1
            self.log = "market lv{}".format(self.market)
            return

        if self.gold >= 70 and self.wood >= 15:
            self.gold -= 70
            self.wood -= 15
            self.guild += 1
            self.log = "guild lv{}".format(self.guild)
            return

        self.log = "need resources"


class UI:
    def __init__(self):
        self.bl = PWM(Pin(13))
        self.bl.freq(1000)
        self.bl.duty_u16(0)

        self.d = lcd.LCD_1inch8()
        self.g = Game()

        self.btn_down = DebouncedButton(Pin(BTN_DOWN_PIN, Pin.IN, Pin.PULL_UP))
        self.btn_select = DebouncedButton(Pin(BTN_SELECT_PIN, Pin.IN, Pin.PULL_UP))
        self.btn_back = DebouncedButton(Pin(BTN_BACK_PIN, Pin.IN, Pin.PULL_UP))

        self.last_draw = time.ticks_ms()
        self.last_auto = time.ticks_ms()

    def clip(self, text):
        if len(text) <= MAX_CHARS:
            return text
        return text[:MAX_CHARS]

    def line(self, y, text, color=COL_INK):
        self.d.text(self.clip(text), 8, y, color)

    def draw_shell(self):
        d = self.d
        d.fill(COL_PARCHMENT)

        # Double page border.
        d.rect(2, 2, d.width - 4, d.height - 4, COL_INK)
        d.rect(4, 4, d.width - 8, d.height - 8, COL_INK)

        # Header banner.
        d.fill_rect(6, 8, d.width - 12, 16, COL_INK)
        self.line(12, "ABYSSAL REALMS", COL_GOLD)

        # Gold separator.
        d.hline(6, 28, d.width - 12, COL_GOLD)

        # Footer nav/help strip.
        d.fill_rect(6, d.height - 18, d.width - 12, 12, COL_INK)
        foot = "{} D/S/B".format(self.g.page)
        self.d.text(self.clip(foot), 8, d.height - 15, COL_GOLD)

    def draw_home(self):
        self.line(36, "Town: {}".format(self.g.town), COL_INK)
        self.line(48, "Day {}   Pop {}".format(self.g.day, self.g.population), COL_INK)
        self.line(60, "Happy {}".format(self.g.happiness), COL_COPPER)
        self.line(74, "G:{} W:{}".format(self.g.gold, self.g.wood), COL_INK)
        self.line(86, "S:{} R:{}".format(self.g.stone, self.g.relics), COL_INK)
        self.line(102, "ACT = next day", COL_COPPER)

    def draw_town(self):
        self.line(36, "TOWN STATUS", COL_GOLD)
        self.line(50, "Houses {}".format(self.g.houses), COL_INK)
        self.line(62, "Farms  {}".format(self.g.farms), COL_INK)
        self.line(74, "Market {}".format(self.g.market), COL_INK)
        self.line(86, "Guild  {}".format(self.g.guild), COL_INK)
        self.line(102, "ACT = rotate town", COL_COPPER)

    def draw_build(self):
        self.line(36, "BUILD ACTION", COL_GOLD)
        self.line(50, "1) Houses 60g 20w", COL_INK)
        self.line(62, "2) Market 80g 18s", COL_INK)
        self.line(74, "3) Guild  70g 15w", COL_INK)
        self.line(90, "Auto priority order", COL_COPPER)
        self.line(102, "ACT = build now", COL_COPPER)

    def draw_log(self):
        self.line(36, "CHRONICLE", COL_GOLD)
        self.line(52, self.g.log, COL_INK)
        self.line(68, "Town {} / {}".format(self.g.town_index + 1, len(TOWNS)), COL_INK)
        self.line(82, "Page {} / {}".format(self.g.page_index + 1, len(PAGES)), COL_INK)
        self.line(102, "ACT = quick tick", COL_COPPER)

    def render(self):
        self.draw_shell()

        if self.g.page == "HOME":
            self.draw_home()
        elif self.g.page == "TOWN":
            self.draw_town()
        elif self.g.page == "BUILD":
            self.draw_build()
        else:
            self.draw_log()

        self.d.show()
        self.bl.duty_u16(54000)

    def handle_input(self):
        _down_now, down_pressed = self.btn_down.update()
        _select_now, select_pressed = self.btn_select.update()
        _back_now, back_pressed = self.btn_back.update()

        if down_pressed:
            self.g.next_page()

        if back_pressed:
            self.g.prev_page()

        if select_pressed:
            if self.g.page == "HOME":
                self.g.tick_day()
            elif self.g.page == "TOWN":
                self.g.next_town()
                self.g.log = "switched town"
            elif self.g.page == "BUILD":
                self.g.try_build()
            else:
                self.g.tick_day()

    def auto_demo(self):
        # Keeps the device alive even if buttons are not connected.
        now = time.ticks_ms()
        if time.ticks_diff(now, self.last_auto) < 2800:
            return
        self.last_auto = now
        self.g.tick_day()

    def run(self):
        self.render()
        while True:
            self.handle_input()
            self.auto_demo()

            now = time.ticks_ms()
            if time.ticks_diff(now, self.last_draw) >= 120:
                self.last_draw = now
                self.render()

            time.sleep_ms(10)


def main():
    UI().run()


if __name__ == "__main__":
    main()
