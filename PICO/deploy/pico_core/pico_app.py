import os
import time
from machine import Pin, PWM  # pyright: ignore[reportMissingImports]

import lcd  # pyright: ignore[reportMissingImports]
from models import (
    default_guild,
    save_game,
    load_game,
    get_slot_info,
    delete_save,
    generate_recruit,
    seed_recruit_pool,
    compute_power,
    compute_party_power,
    apply_training,
    get_available_classes,
    promote_class,
    CLASS_DEFINITIONS,
    can_learn_skill,
    learn_skill,
    SKILL_CATALOG,
    CATEGORY_UNLOCK_GATES,
    unlock_category,
    get_available_missions,
    run_mission,
    tick_update,
    check_guild_rank_up,
    get_guild_rank_title,
)
from pico_input import ADS7830Joystick
from pico_assets import draw_scene_background
from pico_sprites import draw_recruit


COL_BG = 0x0000
COL_PANEL = 0x2104
COL_TEXT = 0xFFFF
COL_DIM = 0xBDF7
COL_ACCENT = 0xFFFF
COL_OK = 0xFFFF
COL_BAD = 0xFFFF
COL_CURSOR = 0xBDF7
COL_SHADE_1 = 0x0000
COL_SHADE_2 = 0x4208


class PicoGuildSim:
    SCENE_ORDER = (
        "save_slots",
        "dashboard",
        "roster",
        "tavern",
        "recruit",
        "missions",
        "training",
        "settings",
        "log",
    )
    SCENE_SHORT = {
        "save_slots": "SV",
        "dashboard": "GH",
        "roster": "RS",
        "tavern": "TV",
        "recruit": "RC",
        "missions": "MS",
        "training": "TR",
        "settings": "MN",
        "log": "LG",
    }
    DASHBOARD_TARGETS = ("roster", "tavern", "missions", "training", "settings", "log", "tick")
    DASHBOARD_NAV = ("Roster", "Tavern", "Quest", "Train", "Menu", "Log", "Tick")
    RECRUIT_TABS = ("Stats", "Train", "Class", "Skill", "Party")
    TRAIN_CATS = ("melee", "magic", "range", "passive")

    def __init__(self):
        self.bl = PWM(Pin(13))
        self.bl.freq(1000)
        self.bl.duty_u16(0)
        self._backlight_ready = False

        self.d = lcd.LCD_1inch8()
        self.input = ADS7830Joystick()
        self.input.calibrate_center()

        self.slot = None
        self.guild = None
        self.roster = []

        self.recruit_pools = {}
        self.available_missions = {}

        self.scene = "save_slots"
        self.cursor = 0
        self.detail_tab = 0
        self.selected_recruit_id = None
        self.message = ""
        self.message_until = 0
        self.scene_switch_mode = False

        self.last_tick_time = time.time()

    def flash(self, text, duration_ms=1700):
        self.message = text[:24]
        self.message_until = time.ticks_add(time.ticks_ms(), duration_ms)

    def ensure_save_dirs(self):
        for s in ("slot1", "slot2", "slot3"):
            path = "saves/" + s
            try:
                os.mkdir(path)
            except OSError:
                pass

    def load_current(self):
        if not self.slot:
            return
        guild, roster = load_game(self.slot)
        self.guild = guild
        self.roster = roster if roster else []

    def save_current(self):
        if self.slot and self.guild is not None:
            save_game(self.slot, self.guild, self.roster)

    def do_tick(self):
        if not self.guild:
            return
        now = time.time()
        elapsed = int(now - self.last_tick_time)
        if elapsed <= 0:
            return
        ticks = min(20, elapsed // 5)
        for _ in range(ticks):
            tick_update(self.guild, self.roster)
        self.last_tick_time = now

    def _active_party(self):
        return [r for r in self.roster if r.get("is_active")]

    def _selected_recruit(self):
        if not self.selected_recruit_id:
            return None
        for r in self.roster:
            if r["id"] == self.selected_recruit_id:
                return r
        return None

    def _ensure_pool(self):
        if self.slot not in self.recruit_pools or len(self.recruit_pools[self.slot]) == 0:
            self.recruit_pools[self.slot] = seed_recruit_pool(self.guild["rank"], 4)

    def _ensure_missions(self):
        if self.slot not in self.available_missions or len(self.available_missions[self.slot]) == 0:
            self.available_missions[self.slot] = get_available_missions(self.guild["rank"])

    def _draw_bg(self):
        # Temporary recovery mode: bypass bitmap backgrounds while panel color
        # calibration is in progress and use a stable solid background.
        self.d.fill(COL_BG)
        # Thin bars: header + nav/footer strip
        self.d.fill_rect(0, 0, 128, 12, COL_SHADE_1)
        self.d.fill_rect(0, 152, 128, 8, COL_SHADE_1)

    def _draw_header(self, title):
        self.d.text(title[:16], 2, 3, COL_ACCENT)
        if self.guild:
            g = str(self.guild.get("gold", 0))
            self.d.text("G:" + g, 82, 3, COL_TEXT)

    def _draw_footer(self):
        # Thin full-width nav bar across bottom.
        x = 1
        for s in self.SCENE_ORDER:
            label = self.SCENE_SHORT[s]
            col = COL_ACCENT if s == self.scene else COL_DIM
            self.d.text(label, x, 152, col)
            x += 14

        mode = "SC" if self.scene_switch_mode else "IN"
        self.d.text(mode, 114, 152, COL_TEXT)

        if self.message and time.ticks_diff(self.message_until, time.ticks_ms()) > 0:
            self.d.fill_rect(0, 136, 128, 10, COL_PANEL)
            self.d.text(self.message, 2, 137, COL_TEXT)

    def _draw_list_cursor(self, row, y0=18, step=12):
        y = y0 + row * step
        self.d.fill_rect(1, y - 1, 126, 10, COL_SHADE_2)
        self.d.rect(1, y - 1, 126, 10, COL_CURSOR)

    def render(self):
        self._draw_bg()
        if self.scene == "save_slots":
            self.render_save_slots()
        elif self.scene == "dashboard":
            self.render_dashboard()
        elif self.scene == "roster":
            self.render_roster()
        elif self.scene == "tavern":
            self.render_tavern()
        elif self.scene == "recruit":
            self.render_recruit_detail()
        elif self.scene == "missions":
            self.render_missions()
        elif self.scene == "training":
            self.render_training()
        elif self.scene == "settings":
            self.render_settings()
        elif self.scene == "log":
            self.render_log()
        self._draw_footer()
        self.d.show()

    def render_save_slots(self):
        self._draw_header("Save Slots")
        slots = ["slot1", "slot2", "slot3"]
        self._draw_list_cursor(self.cursor, y0=20, step=14)
        for i, s in enumerate(slots):
            y = 20 + i * 14
            info = get_slot_info(s)
            if info:
                text = "%s %s" % (s[-1], info["guild_name"][:10])
                self.d.text(text, 4, y, COL_TEXT)
                rt = info["rank_title"][:6]
                self.d.text(rt, 86, y, COL_DIM)
            else:
                self.d.text(s[-1] + " <new>", 4, y, COL_DIM)
        self.d.text("A:Load/New  B:Delete", 2, 66, COL_DIM)

    def render_dashboard(self):
        self._draw_header("Guild Hall")
        rank = get_guild_rank_title(self.guild.get("rank", 1))
        self.d.text(self.guild["name"][:16], 2, 18, COL_TEXT)
        self.d.text(("Lord " + self.guild["lord_name"])[:16], 2, 28, COL_DIM)
        self.d.text(("Rank " + rank)[:16], 2, 38, COL_TEXT)
        self.d.text("M %d/%d" % (self.guild.get("successful_missions", 0), self.guild.get("total_missions", 0)), 2, 48, COL_DIM)

        party = self._active_party()
        self.d.text("Party %d" % len(party), 2, 60, COL_ACCENT)
        for i, m in enumerate(party[:4]):
            x = 2 + i * 30
            draw_recruit(self.d, x, 70, m, scale=1)

        row = self.cursor
        self._draw_list_cursor(row, y0=92, step=9)
        for i, name in enumerate(self.DASHBOARD_NAV):
            self.d.text(name, 4, 92 + i * 9, COL_TEXT if i == row else COL_DIM)

    def render_roster(self):
        self._draw_header("Roster")
        if not self.roster:
            self.d.text("No recruits", 4, 22, COL_DIM)
            self.d.text("Get from tavern", 4, 32, COL_DIM)
            return
        top = max(0, self.cursor - 5)
        vis = self.roster[top:top + 8]
        self._draw_list_cursor(self.cursor - top, y0=20, step=12)
        for i, r in enumerate(vis):
            y = 20 + i * 12
            draw_recruit(self.d, 3, y - 2, r, scale=1)
            name = r["name"][:7]
            lvl = "L%d" % r["level"]
            marker = "*" if r.get("is_active") else "-"
            self.d.text(marker + name, 20, y, COL_TEXT)
            self.d.text(lvl, 88, y, COL_DIM)

    def render_tavern(self):
        self._draw_header("Tavern")
        self._ensure_pool()
        pool = self.recruit_pools[self.slot]
        if not pool:
            self.d.text("Pool empty", 4, 22, COL_DIM)
            return
        max_idx = len(pool)
        if self.cursor > max_idx:
            self.cursor = max_idx
        if self.cursor == max_idx:
            self._draw_list_cursor(max_idx, y0=20, step=12)
        top = max(0, min(self.cursor, len(pool) - 1) - 5)
        vis = pool[top:top + 7]
        for i, r in enumerate(vis):
            y = 20 + i * 12
            row_idx = top + i
            if self.cursor == row_idx:
                self._draw_list_cursor(i, y0=20, step=12)
            draw_recruit(self.d, 3, y - 2, r, scale=1)
            self.d.text(r["name"][:7], 20, y, COL_TEXT)
            self.d.text(str(r["hire_cost"]) + "g", 84, y, COL_ACCENT)
        y = 20 + len(vis) * 12
        label = "[Refresh 20g]"
        c = COL_ACCENT if self.cursor == max_idx else COL_DIM
        self.d.text(label, 4, y, c)

    def render_recruit_detail(self):
        self._draw_header("Recruit")
        r = self._selected_recruit()
        if not r:
            self.d.text("No recruit", 4, 20, COL_DIM)
            return
        draw_recruit(self.d, 2, 18, r, scale=2)
        self.d.text(r["name"][:10], 30, 20, COL_TEXT)
        self.d.text(("L%d " % r["level"] + r["job_class"])[:13], 30, 30, COL_DIM)
        self.d.text("PWR %d" % compute_power(r), 30, 40, COL_ACCENT)

        for i, t in enumerate(self.RECRUIT_TABS):
            x = 2 + i * 25
            col = COL_ACCENT if i == self.detail_tab else COL_DIM
            self.d.text(t[:4], x, 54, col)

        if self.detail_tab == 0:
            self.d.text("HP %d/%d" % (r["current_hp"], r["stats"]["HP"]), 2, 66, COL_TEXT)
            self.d.text("MP %d/%d" % (r["current_mp"], r["stats"]["MP"]), 2, 76, COL_TEXT)
            self.d.text("FTG %d MRL %d" % (r["fatigue"], r["morale"]), 2, 86, COL_DIM)
            self.d.text("M:%d Mg:%d" % (r["training_xp"].get("melee", 0), r["training_xp"].get("magic", 0)), 2, 96, COL_DIM)
            self.d.text("R:%d P:%d" % (r["training_xp"].get("range", 0), r["training_xp"].get("passive", 0)), 2, 106, COL_DIM)
        elif self.detail_tab == 1:
            cat = self.TRAIN_CATS[self.cursor % len(self.TRAIN_CATS)]
            self.d.text("Train: " + cat[:6], 2, 68, COL_TEXT)
            self.d.text("A to train (10g)", 2, 80, COL_DIM)
        elif self.detail_tab == 2:
            classes = get_available_classes(r)
            if not classes:
                self.d.text("No class ready", 2, 68, COL_DIM)
            else:
                cidx = self.cursor % len(classes)
                cname = classes[cidx]
                cost = CLASS_DEFINITIONS[cname]["cost"]
                self.d.text(cname[:12], 2, 68, COL_TEXT)
                self.d.text("Cost %dg" % cost, 2, 80, COL_DIM)
                self.d.text("A promote", 2, 92, COL_DIM)
        elif self.detail_tab == 3:
            unlocked = set(self.guild.get("unlocked_categories", ["melee"]))
            names = [k for k, v in SKILL_CATALOG.items() if v["category"] in unlocked]
            if not names:
                self.d.text("No skills", 2, 68, COL_DIM)
            else:
                sidx = self.cursor % len(names)
                sname = names[sidx]
                can, why = can_learn_skill(r, sname)
                self.d.text(sname[:14], 2, 68, COL_TEXT)
                self.d.text(("OK" if can else "LOCK") + " " + why[:12], 2, 80, COL_DIM)
                self.d.text("A learn", 2, 92, COL_DIM)
        else:
            state = "ACTIVE" if r.get("is_active") else "INACTIVE"
            self.d.text(state, 2, 68, COL_TEXT)
            self.d.text("A toggle party", 2, 80, COL_DIM)
            self.d.text("Hold B release", 2, 92, COL_DIM)

    def render_missions(self):
        self._draw_header("Quest Board")
        self._ensure_missions()
        party = self._active_party()
        self.d.text("PartyPWR %d" % (compute_party_power(party) if party else 0), 2, 18, COL_DIM)

        missions = self.available_missions[self.slot]
        max_idx = len(missions)
        if self.cursor > max_idx:
            self.cursor = max_idx

        top = max(0, min(self.cursor, len(missions) - 1) - 6) if missions else 0
        vis = missions[top:top + 7]

        for i, m in enumerate(vis):
            y = 30 + i * 11
            row_idx = top + i
            if self.cursor == row_idx:
                self._draw_list_cursor(i, y0=30, step=11)
            self.d.text(m["name"][:12], 4, y, COL_TEXT)
            self.d.text("D" + str(m["difficulty"]), 100, y, COL_DIM)

        y = 30 + len(vis) * 11
        c = COL_ACCENT if self.cursor == max_idx else COL_DIM
        self.d.text("[Refresh]", 4, y, c)

    def render_training(self):
        self._draw_header("Training")
        cats = self.TRAIN_CATS
        self._draw_list_cursor(self.cursor, y0=20, step=12)
        for i, cat in enumerate(cats):
            gate = CATEGORY_UNLOCK_GATES[cat]
            unlocked = cat in self.guild.get("unlocked_categories", ["melee"])
            status = "OPEN" if unlocked else ("%dg R%d" % (gate["gold"], gate["guild_rank"]))
            self.d.text(cat[:7], 4, 20 + i * 12, COL_TEXT)
            self.d.text(status[:8], 62, 20 + i * 12, COL_OK if unlocked else COL_DIM)
        self.d.text("A unlock selected", 2, 78, COL_DIM)

        if self.roster:
            ridx = min(len(self.roster) - 1, self.cursor % len(self.roster))
            r = self.roster[ridx]
            draw_recruit(self.d, 2, 90, r, scale=1)
            self.d.text(r["name"][:10], 20, 92, COL_TEXT)
            self.d.text("StickClick:train", 20, 102, COL_DIM)

    def render_settings(self):
        self._draw_header("Guild Menu")
        opts = ["Rename Guild", "Rename Lord", "Quit Save"]
        self._draw_list_cursor(self.cursor, y0=20, step=12)
        for i, o in enumerate(opts):
            self.d.text(o[:15], 4, 20 + i * 12, COL_TEXT)
        self.d.text(("Guild " + self.guild["name"])[:20], 2, 64, COL_DIM)
        self.d.text(("Lord " + self.guild["lord_name"])[:20], 2, 74, COL_DIM)
        self.d.text("A cycles preset names", 2, 86, COL_DIM)

    def render_log(self):
        self._draw_header("Mission Log")
        log = self.guild.get("mission_log", [])
        if not log:
            self.d.text("No logs yet", 4, 20, COL_DIM)
            return
        top = max(0, len(log) - 10 - self.cursor)
        vis = log[top:top + 10]
        for i, line in enumerate(vis):
            self.d.text(line[:20], 2, 20 + i * 12, COL_TEXT if i % 2 == 0 else COL_DIM)

    def _scene_back(self):
        if self.scene == "save_slots":
            return
        if self.scene == "dashboard":
            self.scene = "save_slots"
            self.slot = None
            self.guild = None
            self.roster = []
            self.cursor = 0
            return
        if self.scene == "recruit":
            self.scene = "roster"
            self.cursor = 0
            return
        self.scene = "dashboard"
        self.cursor = 0

    def _handle_save_slots(self, events):
        if events["move"] == "up":
            self.cursor = max(0, self.cursor - 1)
        elif events["move"] == "down":
            self.cursor = min(2, self.cursor + 1)

        if events["a_pressed"]:
            self.slot = "slot%d" % (self.cursor + 1)
            guild, roster = load_game(self.slot)
            if guild is None:
                guild = default_guild("Guild %d" % (self.cursor + 1), "Commander")
                roster = [generate_recruit(1)]
                roster[0]["is_active"] = True
                save_game(self.slot, guild, roster)
                self.flash("New game created")
            self.guild = guild
            self.roster = roster
            self.last_tick_time = time.time()
            self.scene = "dashboard"
            self.cursor = 0

        if events["b_pressed"]:
            slot = "slot%d" % (self.cursor + 1)
            delete_save(slot)
            self.flash("Deleted " + slot)

    def _handle_dashboard(self, events):
        max_row = 6
        if events["move"] == "up":
            self.cursor = max(0, self.cursor - 1)
        elif events["move"] == "down":
            self.cursor = min(max_row, self.cursor + 1)

        if events["a_pressed"]:
            t = self.DASHBOARD_TARGETS[self.cursor]
            if t == "tick":
                tick_update(self.guild, self.roster)
                self.save_current()
                self.flash("+1 tick")
                return
            self.scene = t
            self.cursor = 0

    def _handle_roster(self, events):
        if not self.roster:
            if events["a_pressed"]:
                self.scene = "tavern"
            return
        if events["move"] == "up":
            self.cursor = max(0, self.cursor - 1)
        elif events["move"] == "down":
            self.cursor = min(len(self.roster) - 1, self.cursor + 1)
        if events["a_pressed"]:
            r = self.roster[self.cursor]
            self.selected_recruit_id = r["id"]
            self.detail_tab = 0
            self.cursor = 0
            self.scene = "recruit"

    def _handle_tavern(self, events):
        self._ensure_pool()
        pool = self.recruit_pools[self.slot]
        max_idx = len(pool)
        if events["move"] == "up":
            self.cursor = max(0, self.cursor - 1)
        elif events["move"] == "down":
            self.cursor = min(max_idx, self.cursor + 1)

        if events["a_pressed"]:
            if self.cursor == max_idx:
                if self.guild["gold"] >= 20:
                    self.guild["gold"] -= 20
                    self.recruit_pools[self.slot] = seed_recruit_pool(self.guild["rank"], 4)
                    self.save_current()
                    self.cursor = 0
                    self.flash("Pool refreshed")
                else:
                    self.flash("Need 20g")
                return

            if self.cursor < len(pool):
                recruit = pool[self.cursor]
                if self.guild["gold"] < recruit["hire_cost"]:
                    self.flash("Not enough gold")
                    return
                self.guild["gold"] -= recruit["hire_cost"]
                recruit["recruited_at"] = time.time()
                recruit["is_active"] = len(self._active_party()) == 0
                self.roster.append(recruit)
                pool.pop(self.cursor)
                self.save_current()
                self.flash("Hired " + recruit["name"][:10])

    def _handle_recruit_detail(self, events):
        r = self._selected_recruit()
        if not r:
            self.scene = "roster"
            return

        if events["move"] == "left":
            self.detail_tab = (self.detail_tab - 1) % 5
        elif events["move"] == "right":
            self.detail_tab = (self.detail_tab + 1) % 5
        elif events["move"] == "up":
            self.cursor = max(0, self.cursor - 1)
        elif events["move"] == "down":
            self.cursor += 1

        if self.detail_tab == 1 and events["a_pressed"]:
            cat = self.TRAIN_CATS[self.cursor % len(self.TRAIN_CATS)]
            if cat not in self.guild.get("unlocked_categories", ["melee"]):
                self.flash(cat + " locked")
                return
            if self.guild["gold"] < 10:
                self.flash("Need 10g")
                return
            if r["fatigue"] >= 80 or r["injury_timer"] > 0:
                self.flash("Recruit unavailable")
                return
            self.guild["gold"] -= 10
            gain = apply_training(r, cat)
            self.save_current()
            self.flash("+%d %s xp" % (gain, cat[:2]))

        elif self.detail_tab == 2 and events["a_pressed"]:
            classes = get_available_classes(r)
            if not classes:
                self.flash("No class")
                return
            cname = classes[self.cursor % len(classes)]
            cost = CLASS_DEFINITIONS[cname]["cost"]
            if self.guild["gold"] < cost:
                self.flash("Need %dg" % cost)
                return
            self.guild["gold"] -= cost
            ok, msg = promote_class(r, cname)
            self.save_current()
            self.flash(msg if ok else "Promote failed")

        elif self.detail_tab == 3 and events["a_pressed"]:
            unlocked = set(self.guild.get("unlocked_categories", ["melee"]))
            names = [k for k, v in SKILL_CATALOG.items() if v["category"] in unlocked]
            if not names:
                self.flash("No skills")
                return
            sname = names[self.cursor % len(names)]
            skill_data = SKILL_CATALOG[sname]
            cost = skill_data["cost"]
            if r.get("affinity") == skill_data["category"]:
                cost = int(cost * 0.8)
            if self.guild["gold"] < cost:
                self.flash("Need %dg" % cost)
                return
            ok, msg = learn_skill(r, sname)
            if ok:
                self.guild["gold"] -= cost
                self.save_current()
            self.flash(msg[:24])

        elif self.detail_tab == 4 and events["a_pressed"]:
            active_count = len(self._active_party())
            if r.get("is_active") and active_count <= 1:
                self.flash("Need 1 active")
                return
            if (not r.get("is_active")) and active_count >= 4:
                self.flash("Party full")
                return
            r["is_active"] = not r.get("is_active")
            self.save_current()
            self.flash("Party toggled")

        # Hold B + stick press to release recruit intentionally.
        if events["b_pressed"] and events["stick_pressed"]:
            active_count = len(self._active_party())
            if r.get("is_active") and active_count <= 1:
                self.flash("Cannot release last")
                return
            self.roster.remove(r)
            self.selected_recruit_id = None
            self.save_current()
            self.scene = "roster"
            self.cursor = 0
            self.flash("Released")

    def _handle_missions(self, events):
        self._ensure_missions()
        missions = self.available_missions[self.slot]
        max_idx = len(missions)
        if events["move"] == "up":
            self.cursor = max(0, self.cursor - 1)
        elif events["move"] == "down":
            self.cursor = min(max_idx, self.cursor + 1)

        if events["a_pressed"]:
            if self.cursor == max_idx:
                self.available_missions[self.slot] = get_available_missions(self.guild["rank"])
                self.cursor = 0
                self.flash("Refreshed")
                return

            if self.cursor >= len(missions):
                return
            party = self._active_party()
            if not party:
                self.flash("No active party")
                return
            if [m for m in party if m["injury_timer"] > 0]:
                self.flash("Party injured")
                return

            success, log_lines = run_mission(party, missions[self.cursor], self.guild)
            ranked, msg = check_guild_rank_up(self.guild)
            if ranked:
                log_lines.append(msg)
            self.guild.setdefault("mission_log", []).extend(log_lines)
            if len(self.guild["mission_log"]) > 80:
                self.guild["mission_log"] = self.guild["mission_log"][-80:]
            self.available_missions[self.slot] = get_available_missions(self.guild["rank"])
            self.save_current()
            self.flash("Success" if success else "Failed")

    def _handle_training(self, events):
        cats = self.TRAIN_CATS
        if events["move"] == "up":
            self.cursor = max(0, self.cursor - 1)
        elif events["move"] == "down":
            self.cursor = min(len(cats) - 1, self.cursor + 1)

        if events["a_pressed"]:
            cat = cats[self.cursor]
            ok, msg = unlock_category(self.guild, cat, self.roster)
            if ok:
                self.save_current()
            self.flash(msg[:24])

        if events["stick_pressed"] and self.roster:
            cat = cats[self.cursor]
            r = self.roster[self.cursor % len(self.roster)]
            if cat not in self.guild.get("unlocked_categories", ["melee"]):
                self.flash(cat + " locked")
                return
            if self.guild["gold"] < 10:
                self.flash("Need 10g")
                return
            if r["fatigue"] >= 80 or r["injury_timer"] > 0:
                self.flash("Recruit unavailable")
                return
            self.guild["gold"] -= 10
            gain = apply_training(r, cat)
            self.save_current()
            self.flash("+%d xp" % gain)

    def _cycle_name(self, current, bank):
        try:
            idx = bank.index(current)
        except ValueError:
            idx = -1
        return bank[(idx + 1) % len(bank)]

    def _handle_settings(self, events):
        max_row = 2
        if events["move"] == "up":
            self.cursor = max(0, self.cursor - 1)
        elif events["move"] == "down":
            self.cursor = min(max_row, self.cursor + 1)

        if events["a_pressed"]:
            if self.cursor == 0:
                names = ["Iron Wolves", "Starfall", "Dawnblades", "Ravenmark"]
                self.guild["name"] = self._cycle_name(self.guild["name"], names)
                self.save_current()
                self.flash("Guild renamed")
            elif self.cursor == 1:
                names = ["Commander", "Rex", "Luna", "Nyx", "Theron"]
                self.guild["lord_name"] = self._cycle_name(self.guild["lord_name"], names)
                self.save_current()
                self.flash("Lord renamed")
            else:
                self.save_current()
                self.scene = "save_slots"
                self.slot = None
                self.guild = None
                self.roster = []
                self.cursor = 0
                self.flash("Returned to slots")

    def _handle_log(self, events):
        logs = self.guild.get("mission_log", [])
        max_row = max(0, len(logs) - 1)
        if events["move"] == "up":
            self.cursor = min(max_row, self.cursor + 1)
        elif events["move"] == "down":
            self.cursor = max(0, self.cursor - 1)

    def _switch_scene_lr(self, delta):
        if self.scene not in self.SCENE_ORDER:
            self.scene = "dashboard"
            return
        idx = self.SCENE_ORDER.index(self.scene)
        idx = (idx + delta) % len(self.SCENE_ORDER)
        self.scene = self.SCENE_ORDER[idx]
        self.cursor = 0
        if self.scene == "recruit" and self.roster:
            self.selected_recruit_id = self.roster[0]["id"]

    def handle_input(self, events):
        if self.scene == "save_slots":
            self._handle_save_slots(events)
            return

        release_combo = self.scene == "recruit" and events["b_pressed"] and events["stick_pressed"]
        if events["stick_pressed"] and not events["b_pressed"] and not release_combo:
            self.scene_switch_mode = not self.scene_switch_mode
            self.flash("Scene LR" if self.scene_switch_mode else "Scene Ctrl")
            return

        if self.scene_switch_mode and events["move"] in ("left", "right"):
            self._switch_scene_lr(-1 if events["move"] == "left" else 1)
            return

        if events["b_pressed"] and not events["stick_pressed"]:
            self._scene_back()
            return

        if self.scene == "dashboard":
            self._handle_dashboard(events)
        elif self.scene == "roster":
            self._handle_roster(events)
        elif self.scene == "tavern":
            self._handle_tavern(events)
        elif self.scene == "recruit":
            self._handle_recruit_detail(events)
        elif self.scene == "missions":
            self._handle_missions(events)
        elif self.scene == "training":
            self._handle_training(events)
        elif self.scene == "settings":
            self._handle_settings(events)
        elif self.scene == "log":
            self._handle_log(events)

    def run(self):
        self.ensure_save_dirs()
        while True:
            self.do_tick()
            events = self.input.poll()
            self.handle_input(events)
            self.render()
            if not self._backlight_ready:
                self.bl.duty_u16(42000)
                self._backlight_ready = True
            time.sleep_ms(40)


def main():
    PicoGuildSim().run()


if __name__ == "__main__":
    main()
