"""Quick non-interactive smoke checks for Thonny-first development."""

from campaign_stream import extract_meta
from collection_book import load_collection, record_hof, record_item, record_monster
from game_paths import ROSTER_FILE, SW25_CAMPAIGNS_DIR
from guild_rules import blocked_skill_categories, try_unlock_category
from integrity import build_manifest, validate_json_file
from kernel_core import PATHS, ensure_runtime_dirs
from roster_manager import load_roster, save_roster, active_party
from storage import load_json, save_json, get_data_root
from sw25_math import success_value, k_table_damage
from watch_system import apply_mission_attrition, tick_recruit


def assert_true(condition, label):
    if not condition:
        raise AssertionError(label)
    print("PASS:", label)


def main():
    root = ensure_runtime_dirs()
    print("Data root:", root)

    # Storage write/read sanity.
    save_json("game_core/smoke_tmp.json", {"ok": True, "v": 1})
    data = load_json("game_core/smoke_tmp.json", {})
    assert_true(data.get("ok") is True, "storage read/write")

    # Collection ledger hooks.
    record_monster("Smoke Slime", "smoke")
    record_item("Smoke Sword", "test", "smoke")
    record_hof("Smoke Hero", "tester", "smoke run")
    coll = load_collection()
    assert_true(len(coll.get("monster_manual", [])) >= 1, "collection monster append")
    assert_true(len(coll.get("item_ledger", [])) >= 1, "collection item append")
    assert_true(len(coll.get("hall_of_fame", [])) >= 1, "collection hall of fame append")

    # SW math helpers.
    sv = success_value(roll_2d6=7, class_level=2, modifier=1, target_number=10)
    assert_true(sv["total"] == 10 and sv["success"] is True, "success value math")
    kd = k_table_damage(power=30, roll=8)
    assert_true(kd >= 0, "k-table non-negative")

    # Roster + rules + watch systems.
    roster = load_roster()
    save_roster(roster)
    party = active_party(roster)
    assert_true(len(party) >= 1, "active party exists")
    recruit = party[0]
    before_fatigue = int(recruit.get("equipment_fatigue", 0))
    tick_recruit(recruit)
    apply_mission_attrition(recruit, mission_difficulty=2)
    assert_true(int(recruit.get("equipment_fatigue", 0)) > before_fatigue, "fatigue tick and mission attrition")

    # Category unlock gates (expected to fail with default data, but should return reason).
    guild = load_json("guild_sim/guild.json", {"gold": 0, "rank": 1, "unlocked_categories": ["Melee"]})
    ok, reason = try_unlock_category(guild, roster, "Magic")
    assert_true(reason in ("unlocked", "already-unlocked", "gold-too-low", "rank-too-low", "roster-xp-too-low"), "unlock gate returns reason")

    # Campaign stream and integrity.
    sample_rel = SW25_CAMPAIGNS_DIR + "/starter_ruins.json"
    sample_abs = get_data_root() + "/" + sample_rel
    # Ensure sample file exists for parser smoke.
    campaign_data = {
        "title": "Starter Ruins",
        "target_number": 10,
        "notes": "Smoke campaign",
    }
    save_json(sample_rel, campaign_data)
    meta = extract_meta(sample_abs)
    assert_true(meta.get("target_number") == 10, "campaign stream metadata parse")

    manifest = build_manifest([sample_rel, PATHS["collection_book"], ROSTER_FILE])
    assert_true(sample_rel in manifest, "manifest build includes campaign")

    ok_json, reason_json = validate_json_file(sample_rel)
    assert_true(ok_json is True and reason_json == "ok", "manifest + json validate")

    print("ALL SMOKE CHECKS PASSED")


if __name__ == "__main__":
    main()
