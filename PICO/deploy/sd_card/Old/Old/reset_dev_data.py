"""Reset development save data while keeping source files intact."""

from kernel_core import PATHS, ensure_runtime_dirs
from storage import save_json, get_data_root


DEFAULT_GUILD = {
    "guild_name": "Goldenhaven",
    "lord": "Aldric",
    "rank": 1,
    "gold": 5000,
    "soul_gems": 75000,
    "unlocked_categories": ["Melee"],
}


DEFAULT_ROSTER = {
    "recruits": [
        {
            "id": "stan",
            "name": "Stan",
            "class": "Novice",
            "affinity": "Combat",
            "xp": 0,
            "stats": {"STR": 10, "DEX": 10, "AGI": 10, "INT": 10, "VIT": 10, "SPR": 10},
            "training_lvls": {"Melee": 1, "Magic": 0, "Range": 0, "Passive": 0},
            "eligible_to_buy": [],
            "learned_skills": [],
            "archive_unlocked": [],
            "weapon_type": "sword",
            "armor_weight": "medium",
            "injury_until": 0,
            "equipment_fatigue": 0,
        }
    ],
    "active_party_ids": ["stan"],
}


DEFAULT_SW25 = {
    "name": "New Character",
    "class": "Fighter",
    "level": 1,
    "terminology": "official",
    "is_fellow": False,
    "stats": {"STR": 10, "DEX": 10, "AGI": 10, "INT": 10, "VIT": 10, "SPR": 10},
    "sheet_image": "assets/sw25_character_sheet.png",
}


DEFAULT_COLLECTION = {
    "monster_manual": [],
    "item_ledger": [],
    "hall_of_fame": [],
}


def main():
    root = ensure_runtime_dirs()

    save_json(PATHS["guild_sim"] + "/guild.json", dict(DEFAULT_GUILD))
    save_json(PATHS["guild_sim"] + "/roster.json", dict(DEFAULT_ROSTER))
    save_json(PATHS["sw25"] + "/character.json", dict(DEFAULT_SW25))
    save_json(PATHS["collection_book"], dict(DEFAULT_COLLECTION))
    save_json(PATHS["manifest"], {})

    # Keep starter campaign present after reset.
    save_json(
        PATHS["sw25_campaigns"] + "/starter_ruins.json",
        {
            "title": "Starter Ruins",
            "target_number": 10,
            "notes": "Simple intro encounter. Add files to sw25/campaigns as JSON.",
        },
    )

    print("Reset complete at data root:", root)


if __name__ == "__main__":
    main()
