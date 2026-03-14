import random
import time
import os

from collection_book import record_hof, record_item, record_monster
from game_paths import GUILD_FILE, ROSTER_FILE
from guild_rules import blocked_skill_categories, try_unlock_category
from integrity import build_manifest
from kernel_core import PATHS
from mission_log import append_log_line, tail_log
from pc_menu import Menu, read_command
from roster_manager import (
    DEFAULT_ROSTER,
    active_party,
    add_recruit,
    add_to_active_party,
    get_recruit,
    load_roster,
    new_recruit,
    remove_from_active_party,
    remove_recruit,
    save_roster,
)
from seed_world import rename_guild, seed_campaign_templates, seed_recruit_pool
from skills_catalog import all_skills, category_summary, find_skill
from storage import load_json, save_json, ensure_dir, get_data_root
from watch_system import tick_recruit, apply_mission_attrition
import ui_theme


DEFAULT_GUILD = {
    "guild_name": "Goldenhaven",
    "lord": "Aldric",
    "rank": 1,
    "gold": 5000,
    "soul_gems": 75000,
    "unlocked_categories": ["Melee"],
}


CATEGORY_MAP = {
    "Melee": ("STR", "VIT", "DEX"),
    "Magic": ("INT", "SPR", "AGI"),
    "Range": ("DEX", "AGI", "STR"),
    "Passive": ("VIT", "SPR", "INT"),
}


CLASS_STORE = {
    "Warrior": {"category": "Melee", "level": 5, "cost": 2000},
    "Knight": {"category": "Melee", "level": 10, "cost": 5000},
    "Mage": {"category": "Magic", "level": 5, "cost": 2200},
    "Ranger": {"category": "Range", "level": 5, "cost": 2200},
}


SLOT_IDS = ["slot1", "slot2", "slot3"]


def _slot_paths(slot_id):
    base = "guild_sim/slots/{}".format(slot_id)
    return {
        "base": base,
        "guild": base + "/guild.json",
        "roster": base + "/roster.json",
    }


def list_slot_status():
    root = get_data_root()
    results = []
    for slot_id in SLOT_IDS:
        paths = _slot_paths(slot_id)
        full = root + "/" + paths["guild"]
        exists = os.path.exists(full)
        if exists:
            guild = load_json(paths["guild"], dict(DEFAULT_GUILD))
            label = "{} | {} | rank {} | {}g".format(
                guild.get("guild_name", "Guild"),
                guild.get("lord", "Guild Master"),
                guild.get("rank", 1),
                guild.get("gold", 0),
            )
        else:
            label = "<empty>"
        results.append({"slot": slot_id, "exists": exists, "label": label})
    return results


def init_new_game_slot(slot_id):
    paths = _slot_paths(slot_id)
    ensure_dir(get_data_root() + "/" + paths["base"])
    save_json(paths["guild"], dict(DEFAULT_GUILD))
    save_roster(dict(DEFAULT_ROSTER), paths["roster"])


def slot_exists(slot_id):
    root = get_data_root()
    return os.path.exists(root + "/" + _slot_paths(slot_id)["guild"])


def _normalize_guild(guild):
    guild.setdefault("guild_name", DEFAULT_GUILD["guild_name"])
    guild.setdefault("lord", DEFAULT_GUILD["lord"])
    guild.setdefault("rank", DEFAULT_GUILD["rank"])
    guild.setdefault("gold", DEFAULT_GUILD["gold"])
    guild.setdefault("soul_gems", DEFAULT_GUILD["soul_gems"])
    guild.setdefault("unlocked_categories", list(DEFAULT_GUILD["unlocked_categories"]))


def _normalize_recruit(recruit):
    recruit.setdefault("name", "Unknown")
    recruit.setdefault("class", "Novice")
    recruit.setdefault("affinity", random.choice(["Combat", "Magic", "Utility", "Passive"]))
    recruit.setdefault("xp", 0)
    recruit.setdefault("stats", {"STR": 10, "DEX": 10, "AGI": 10, "INT": 10, "VIT": 10, "SPR": 10})
    recruit.setdefault("training_lvls", {"Melee": 0, "Magic": 0, "Range": 0, "Passive": 0})
    recruit.setdefault("eligible_to_buy", [])
    recruit.setdefault("learned_skills", [])
    recruit.setdefault("archive_unlocked", [])
    recruit.setdefault("weapon_type", "sword")
    recruit.setdefault("armor_weight", "medium")
    recruit.setdefault("injury_until", 0)
    recruit.setdefault("equipment_fatigue", 0)


def _unlock_by_training(recruit):
    for class_name, rule in CLASS_STORE.items():
        category = rule["category"]
        if recruit["training_lvls"].get(category, 0) >= rule["level"]:
            if class_name not in recruit["eligible_to_buy"]:
                recruit["eligible_to_buy"].append(class_name)
                print("Class unlocked for purchase: {}".format(class_name))


def _effective_skill_cost(recruit, skill):
    cost = int(skill["cost"])
    if recruit.get("affinity") == skill.get("category"):
        cost = int(cost * 0.7)
    return cost


def _is_locked_for_recruit(recruit, skill):
    if not skill.get("locked"):
        return False
    return skill["name"] not in recruit["archive_unlocked"]


def _blocked_by_gear(recruit, skill):
    blocked = blocked_skill_categories(recruit.get("weapon_type", "sword"), recruit.get("armor_weight", "medium"))
    if skill.get("category") not in blocked:
        return False
    return skill.get("rank") in ("A", "B", "S")


def _print_dashboard(guild, roster, recruit):
    ui_theme.clear_pad(3)
    ui_theme.header("KINGDOM DASHBOARD")
    ui_theme.kv("Lord", guild["lord"])
    ui_theme.kv("Kingdom", guild["guild_name"])
    ui_theme.kv("Year", "1")
    ui_theme.section("RESOURCES")
    ui_theme.kv("Gold", guild["gold"])
    ui_theme.kv("Soul Gems", guild["soul_gems"])
    ui_theme.kv("Rank", guild["rank"])
    ui_theme.kv("Unlocked Categories", guild["unlocked_categories"])
    ui_theme.section("ACTIVE TASKS")
    ui_theme.kv("Active Party Size", len(active_party(roster)))
    ui_theme.kv("Selected Recruit", "{} ({})".format(recruit["name"], recruit["class"]))
    ui_theme.kv("Weapon/Armor", "{}/{}".format(recruit.get("weapon_type", "?"), recruit.get("armor_weight", "?")))
    ui_theme.kv("Equipment Fatigue", recruit.get("equipment_fatigue", 0))
    ui_theme.kv("Injury Timer", recruit.get("injury_until", 0))
    print("=" * 70)


def _show_stats(recruit):
    stats = recruit["stats"]
    print(
        "Class: {} | Affinity:{} | XP:{} | STR:{} DEX:{} AGI:{} INT:{} VIT:{} SPR:{}".format(
            recruit["class"],
            recruit["affinity"],
            recruit.get("xp", 0),
            stats["STR"],
            stats["DEX"],
            stats["AGI"],
            stats["INT"],
            stats["VIT"],
            stats["SPR"],
        )
    )


def _list_skills_brief(recruit):
    ui_theme.header("SKILL ARCHIVE")
    ui_theme.kv("Category Totals", category_summary())
    ui_theme.kv("Skill Count", len(all_skills()))
    ui_theme.section("SKILLS")
    for skill in all_skills():
        lock_text = "LOCKED" if _is_locked_for_recruit(recruit, skill) else "OPEN"
        blocked_text = " BLOCKED" if _blocked_by_gear(recruit, skill) else ""
        ui_theme.bullet(
            "{} [{}] {} gems ({}){}".format(
                skill["name"], skill["rank"], _effective_skill_cost(recruit, skill), lock_text, blocked_text
            )
        )


def _show_learned_skills(recruit):
    if not recruit["learned_skills"]:
        print("No learned skills yet.")
        return
    ui_theme.header("LEARNED SKILLS")
    for name in recruit["learned_skills"]:
        ui_theme.bullet(name)


def run(slot_id=None, new_game=False):
    if slot_id:
        slot = _slot_paths(slot_id)
        guild_file = slot["guild"]
        roster_file = slot["roster"]
        if new_game or not slot_exists(slot_id):
            init_new_game_slot(slot_id)
    else:
        guild_file = GUILD_FILE
        roster_file = ROSTER_FILE

    guild = load_json(guild_file, dict(DEFAULT_GUILD))
    roster = load_roster(roster_file)
    _normalize_guild(guild)

    for recruit in roster.get("recruits", []):
        _normalize_recruit(recruit)

    active_ids = roster.get("active_party_ids", [])
    selected_index = {"value": 0}

    def selected_recruit():
        party = active_party(roster)
        if not party:
            # Fallback to first recruit if active list gets empty.
            recruits = roster.get("recruits", [])
            if recruits:
                roster["active_party_ids"] = [recruits[0]["id"]]
                party = [recruits[0]]
            else:
                raise RuntimeError("Roster has no recruits")
        selected_index["value"] %= len(party)
        return party[selected_index["value"]]

    running = {"value": True}
    last_watch = time.time()

    def save_all():
        save_json(guild_file, guild)
        save_roster(roster, roster_file)
        print("Saved guild_sim data.")

    def list_roster():
        ui_theme.header("ROSTER")
        party_ids = set(roster.get("active_party_ids", []))
        for recruit in roster.get("recruits", []):
            state = "ACTIVE" if recruit.get("id") in party_ids else "RESERVE"
            ui_theme.bullet(
                "{} [{}] Class:{} XP:{} Fatigue:{} Injury:{}".format(
                    recruit.get("name"),
                    state,
                    recruit.get("class"),
                    recruit.get("xp", 0),
                    recruit.get("equipment_fatigue", 0),
                    recruit.get("injury_until", 0),
                )
            )

    def rename_guild_flow():
        new_guild_name = input("Guild name > ").strip()
        new_lord_name = input("Guild master name > ").strip()
        rename_guild(guild, new_guild_name or None, new_lord_name or None)
        print("Guild renamed: {} | Lord: {}".format(guild.get("guild_name"), guild.get("lord")))

    def seed_recruit_pool_flow():
        try:
            count = int(input("How many recruits to seed? (default 5) > ").strip() or "5")
        except Exception:
            count = 5
        added = seed_recruit_pool(roster, count=count)
        print("Seeded recruits added:", added)

    def seed_campaign_templates_flow():
        try:
            count = int(input("How many campaign templates? (1-5) > ").strip() or "3")
        except Exception:
            count = 3
        created = seed_campaign_templates(count=count)
        print("Seeded campaigns:")
        for rel in created:
            print("-", rel)

    def hire_recruit_flow():
        name = input("Recruit name > ").strip()
        if not name:
            print("Name is required.")
            return
        affinity = input("Affinity (Combat/Magic/Utility/Passive or blank random) > ").strip().title()
        recruit = new_recruit(name, affinity or None)
        ok, reason = add_recruit(roster, recruit)
        print("Hire {} => {}".format(name, reason))
        if ok and len(active_party(roster)) < 4:
            add_to_active_party(roster, recruit["id"])

    def assign_party_member_flow():
        recruit_id = input("Recruit id to add active party > ").strip().lower().replace(" ", "_")
        ok, reason = add_to_active_party(roster, recruit_id)
        print("Assign party => {}".format(reason))

    def remove_party_member_flow():
        recruit_id = input("Recruit id to remove from active party > ").strip().lower().replace(" ", "_")
        ok, reason = remove_from_active_party(roster, recruit_id)
        print("Remove party => {}".format(reason))

    def release_recruit_flow():
        recruit_id = input("Recruit id to remove from guild roster > ").strip().lower().replace(" ", "_")
        if recruit_id == selected_recruit().get("id") and len(active_party(roster)) <= 1:
            print("Cannot remove last active recruit.")
            return
        ok, reason = remove_recruit(roster, recruit_id)
        print("Release recruit => {}".format(reason))

    def cycle_recruit():
        party = active_party(roster)
        if not party:
            print("No active party members.")
            return
        selected_index["value"] = (selected_index["value"] + 1) % len(party)
        print("Selected recruit: {}".format(selected_recruit()["name"]))

    def view_dashboard():
        _print_dashboard(guild, roster, selected_recruit())

    def train_category(category):
        recruit = selected_recruit()
        if category not in guild.get("unlocked_categories", []):
            print("Category is locked at guild level.")
            return
        cost = 100
        if guild["gold"] < cost:
            print("Not enough gold for training.")
            return
        guild["gold"] -= cost
        recruit["training_lvls"][category] += 1
        recruit["xp"] = int(recruit.get("xp", 0)) + 10
        primary, secondary, tertiary = CATEGORY_MAP[category]
        recruit["stats"][primary] += 2
        recruit["stats"][secondary] += 1
        recruit["stats"][tertiary] += 1
        print("{} trained {} to Lvl {}".format(recruit["name"], category, recruit["training_lvls"][category]))
        _unlock_by_training(recruit)

    def train_melee():
        train_category("Melee")

    def train_magic():
        train_category("Magic")

    def train_range():
        train_category("Range")

    def train_passive():
        train_category("Passive")

    def unlock_category_flow():
        category = input("Unlock category (Magic/Range/Passive) > ").strip().title()
        ok, reason = try_unlock_category(guild, roster, category)
        print("Unlock {} => {}".format(category, reason if not ok else "success"))

    def buy_class(class_name):
        recruit = selected_recruit()
        if class_name not in CLASS_STORE:
            print("Unknown class.")
            return
        entry = CLASS_STORE[class_name]
        if class_name not in recruit["eligible_to_buy"]:
            print("Class not unlocked yet.")
            return
        if guild["gold"] < entry["cost"]:
            print("Not enough gold.")
            return
        guild["gold"] -= entry["cost"]
        recruit["class"] = class_name
        record_item("Class License: " + class_name, "class", "guild_sim")
        print("Purchased class: {}".format(class_name))

    def buy_warrior():
        buy_class("Warrior")

    def buy_knight():
        buy_class("Knight")

    def buy_mage():
        buy_class("Mage")

    def buy_ranger():
        buy_class("Ranger")

    def equip_loadout():
        recruit = selected_recruit()
        weapon = input("Weapon (sword/staff/bow) > ").strip().lower() or recruit.get("weapon_type", "sword")
        armor = input("Armor (light/medium/heavy) > ").strip().lower() or recruit.get("armor_weight", "medium")
        recruit["weapon_type"] = weapon
        recruit["armor_weight"] = armor
        blocked = blocked_skill_categories(weapon, armor)
        print("Blocked skill categories due to loadout: {}".format(blocked if blocked else "none"))

    def show_skill_catalog():
        _list_skills_brief(selected_recruit())

    def unlock_archive_skill():
        recruit = selected_recruit()
        locked = [s for s in all_skills() if s.get("locked") and s["name"] not in recruit["archive_unlocked"]]
        if not locked:
            print("No locked archive skills remain.")
            return
        for skill in locked:
            print("- {} (unlock: {} gems)".format(skill["name"], skill["cost"] * 2))
        choice = input("Unlock which skill name? > ").strip()
        selected = find_skill(choice)
        if not selected or not selected.get("locked"):
            print("Invalid archive skill.")
            return
        if selected["name"] in recruit["archive_unlocked"]:
            print("Already unlocked.")
            return
        unlock_cost = selected["cost"] * 2
        if guild["soul_gems"] < unlock_cost:
            print("Not enough soul gems.")
            return
        guild["soul_gems"] -= unlock_cost
        recruit["archive_unlocked"].append(selected["name"])
        print("Archive unlocked: {}".format(selected["name"]))

    def learn_skill():
        recruit = selected_recruit()
        choice = input("Learn which skill name? > ").strip()
        selected = find_skill(choice)
        if not selected:
            print("Skill not found.")
            return
        if selected["name"] in recruit["learned_skills"]:
            print("Skill already learned.")
            return
        if _is_locked_for_recruit(recruit, selected):
            print("Skill is locked in Heavenly Archive. Unlock first.")
            return
        if _blocked_by_gear(recruit, selected):
            print("Skill blocked by current weapon/armor restrictions.")
            return
        cost = _effective_skill_cost(recruit, selected)
        if guild["soul_gems"] < cost:
            print("Not enough soul gems.")
            return
        guild["soul_gems"] -= cost
        recruit["learned_skills"].append(selected["name"])
        print("Learned skill: {} (cost {})".format(selected["name"], cost))

    def show_learned_skills():
        _show_learned_skills(selected_recruit())

    def check_stats():
        _show_stats(selected_recruit())

    def mission_attrition_demo():
        recruit = selected_recruit()
        try:
            diff = int(input("Mission difficulty (1-4) > ").strip() or "1")
        except Exception:
            diff = 1
        apply_mission_attrition(recruit, diff)
        record_monster("Field Encounter T{}".format(diff), "guild_sim")
        print("Mission attrition applied.")

    def run_quest_simulation():
        party = active_party(roster)
        if not party:
            print("No active party available.")
            return

        try:
            diff = int(input("Quest difficulty (1-5) > ").strip() or "1")
        except Exception:
            diff = 1
        diff = max(1, min(5, diff))

        log_name = None
        log_name = append_log_line("[b]Quest Start[/b] difficulty={}".format(diff), log_name)

        total_power = 0
        for recruit in party:
            if int(recruit.get("injury_until", 0)) > int(time.time()):
                append_log_line("{} is injured and contributes less.".format(recruit["name"]), log_name)
                total_power += int(recruit["stats"].get("VIT", 0) // 2)
            else:
                recruit_power = (
                    int(recruit["stats"].get("STR", 0))
                    + int(recruit["stats"].get("DEX", 0))
                    + int(recruit["stats"].get("INT", 0))
                )
                total_power += recruit_power
            apply_mission_attrition(recruit, diff)

        encounter_roll = random.randint(8, 20) * diff
        success = total_power >= encounter_roll
        append_log_line(
            "Party power={} vs encounter={} => {}".format(
                total_power, encounter_roll, "SUCCESS" if success else "FAIL"
            ),
            log_name,
        )

        if success:
            reward_gold = diff * 300
            reward_gems = diff * 120
            guild["gold"] += reward_gold
            guild["soul_gems"] += reward_gems
            for recruit in party:
                recruit["xp"] = int(recruit.get("xp", 0)) + (diff * 20)
            record_item("Quest Reward Crate T{}".format(diff), "tier{}".format(diff), "guild_sim")
            record_monster("Quest Target T{}".format(diff), "guild_sim")
            append_log_line("Rewards: +{} gold, +{} gems".format(reward_gold, reward_gems), log_name)
            print("Quest success. Rewards granted.")
        else:
            guild["gold"] = max(0, guild["gold"] - (diff * 100))
            append_log_line("Quest failed. Recovery costs applied.", log_name)
            print("Quest failed. Recovery costs applied.")

        append_log_line("[i]Quest End[/i]", log_name)
        print("Mission log file:", log_name)

    def show_recent_log():
        log_name = input("Log file name (blank for latest timestamp if known) > ").strip()
        if not log_name:
            print("Provide a specific log file name from quest output.")
            return
        try:
            ui_theme.header("MISSION LOG TAIL")
            for line in tail_log(log_name, max_lines=20):
                print(line)
        except Exception as exc:
            print("Unable to read log:", exc)

    def retire_selected_to_hof():
        recruit = selected_recruit()
        record_hof(recruit["name"], "guild_adventurer", "Retired from active party")
        print("Retired recruit recorded in hall of fame.")

    def rebuild_manifest():
        rel_paths = [GUILD_FILE, ROSTER_FILE, PATHS["collection_book"]]
        manifest = build_manifest(rel_paths)
        print("Manifest entries: {}".format(len(manifest)))

    def exit_kernel():
        save_all()
        running["value"] = False

    menu = Menu(
        [
            {
                "label": lambda: "Gold:{}g Gems:{} Rank:{} Party:{} Selected:{}".format(
                    guild["gold"], guild["soul_gems"], guild["rank"], len(active_party(roster)), selected_recruit()["name"]
                ),
                "action": lambda: None,
            },
            {"label": "View Dashboard", "action": view_dashboard},
            {"label": "Rename Guild", "action": rename_guild_flow},
            {"label": "List Roster", "action": list_roster},
            {"label": "Hire Recruit", "action": hire_recruit_flow},
            {"label": "Seed Recruit Pool", "action": seed_recruit_pool_flow},
            {"label": "Assign Recruit To Party", "action": assign_party_member_flow},
            {"label": "Remove Recruit From Party", "action": remove_party_member_flow},
            {"label": "Release Recruit", "action": release_recruit_flow},
            {"label": "Cycle Active Recruit", "action": cycle_recruit},
            {"label": "Seed SW2.5 Campaign Templates", "action": seed_campaign_templates_flow},
            {"label": "Unlock Category (Guild Rules)", "action": unlock_category_flow},
            {"label": "Train Melee (100g)", "action": train_melee},
            {"label": "Train Magic (100g)", "action": train_magic},
            {"label": "Train Range (100g)", "action": train_range},
            {"label": "Train Passive (100g)", "action": train_passive},
            {"label": "Buy Warrior (2000g)", "action": buy_warrior},
            {"label": "Buy Knight (5000g)", "action": buy_knight},
            {"label": "Buy Mage (2200g)", "action": buy_mage},
            {"label": "Buy Ranger (2200g)", "action": buy_ranger},
            {"label": "Equip Weapon/Armor", "action": equip_loadout},
            {"label": "View Skill Catalog", "action": show_skill_catalog},
            {"label": "Unlock Archive Skill", "action": unlock_archive_skill},
            {"label": "Learn Skill", "action": learn_skill},
            {"label": "Show Learned Skills", "action": show_learned_skills},
            {"label": "Check Stats", "action": check_stats},
            {"label": "Mission Attrition Demo", "action": mission_attrition_demo},
            {"label": "Run Quest Simulation", "action": run_quest_simulation},
            {"label": "View Mission Log Tail", "action": show_recent_log},
            {"label": "Retire Recruit to Hall of Fame", "action": retire_selected_to_hof},
            {"label": "Rebuild Integrity Manifest", "action": rebuild_manifest},
            {"label": "Save", "action": save_all},
            {"label": "Back to Launcher", "action": exit_kernel},
        ],
        title="ISEKAI GUILD SIM",
    )

    menu.display()

    while running["value"]:
        now = time.time()
        if now - last_watch >= 10:
            for recruit in active_party(roster):
                tick_recruit(recruit, now)
            last_watch = now
            print("Watch tick: active party recovery and fatigue update.")

        cmd = read_command()
        if cmd == "w":
            menu.move(-1)
        elif cmd == "s":
            menu.move(1)
        elif cmd in ("", "e", "enter"):
            menu.select()
            if running["value"]:
                menu.display()
        elif cmd == "q":
            exit_kernel()
        else:
            print("Unknown command. Use w/s/enter/q.")
