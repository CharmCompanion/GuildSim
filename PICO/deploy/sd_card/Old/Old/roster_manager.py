"""Party roster virtualization helpers (1-4 active party)."""

import random

from game_paths import ROSTER_FILE
from storage import load_json, save_json


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


def load_roster(rel_path=ROSTER_FILE):
    roster = load_json(rel_path, dict(DEFAULT_ROSTER))
    roster.setdefault("recruits", [])
    roster.setdefault("active_party_ids", [])
    return roster


def save_roster(roster, rel_path=ROSTER_FILE):
    save_json(rel_path, roster)


def active_party(roster):
    ids = set(roster.get("active_party_ids", []))
    return [r for r in roster.get("recruits", []) if r.get("id") in ids]


def inactive_recruits(roster):
    ids = set(roster.get("active_party_ids", []))
    return [r for r in roster.get("recruits", []) if r.get("id") not in ids]


def set_active_party(roster, ids):
    roster["active_party_ids"] = list(ids)[:4]


def get_recruit(roster, recruit_id):
    for recruit in roster.get("recruits", []):
        if recruit.get("id") == recruit_id:
            return recruit
    return None


def new_recruit(name, affinity=None):
    affinity = affinity or random.choice(["Combat", "Magic", "Utility", "Passive"])
    clean_id = name.strip().lower().replace(" ", "_")
    return {
        "id": clean_id,
        "name": name,
        "class": "Novice",
        "affinity": affinity,
        "xp": 0,
        "stats": {"STR": 10, "DEX": 10, "AGI": 10, "INT": 10, "VIT": 10, "SPR": 10},
        "training_lvls": {"Melee": 0, "Magic": 0, "Range": 0, "Passive": 0},
        "eligible_to_buy": [],
        "learned_skills": [],
        "archive_unlocked": [],
        "weapon_type": "sword",
        "armor_weight": "medium",
        "injury_until": 0,
        "equipment_fatigue": 0,
    }


def add_recruit(roster, recruit):
    recruits = roster.setdefault("recruits", [])
    if get_recruit(roster, recruit.get("id")):
        return False, "duplicate-id"
    recruits.append(recruit)
    return True, "added"


def remove_recruit(roster, recruit_id):
    recruits = roster.get("recruits", [])
    for idx, recruit in enumerate(recruits):
        if recruit.get("id") == recruit_id:
            recruits.pop(idx)
            roster["active_party_ids"] = [rid for rid in roster.get("active_party_ids", []) if rid != recruit_id]
            return True, "removed"
    return False, "not-found"


def add_to_active_party(roster, recruit_id):
    if not get_recruit(roster, recruit_id):
        return False, "not-found"
    party_ids = roster.setdefault("active_party_ids", [])
    if recruit_id in party_ids:
        return False, "already-active"
    if len(party_ids) >= 4:
        return False, "party-full"
    party_ids.append(recruit_id)
    return True, "added"


def remove_from_active_party(roster, recruit_id):
    party_ids = roster.setdefault("active_party_ids", [])
    if recruit_id not in party_ids:
        return False, "not-active"
    party_ids.remove(recruit_id)
    return True, "removed"
