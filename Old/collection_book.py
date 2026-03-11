"""Shared collection ledger: monsters, items, hall of fame."""

from kernel_core import PATHS
from storage import load_json, save_json


DEFAULT_COLLECTION = {
    "monster_manual": [],
    "item_ledger": [],
    "hall_of_fame": [],
}


def load_collection():
    data = load_json(PATHS["collection_book"], dict(DEFAULT_COLLECTION))
    data.setdefault("monster_manual", [])
    data.setdefault("item_ledger", [])
    data.setdefault("hall_of_fame", [])
    return data


def save_collection(data):
    save_json(PATHS["collection_book"], data)


def record_monster(name, source="unknown"):
    data = load_collection()
    entry = {"name": name, "source": source}
    if entry not in data["monster_manual"]:
        data["monster_manual"].append(entry)
        save_collection(data)


def record_item(name, tier="base", source="unknown"):
    data = load_collection()
    entry = {"name": name, "tier": tier, "source": source}
    data["item_ledger"].append(entry)
    save_collection(data)


def record_hof(name, role, note=""):
    data = load_collection()
    data["hall_of_fame"].append({"name": name, "role": role, "note": note})
    save_collection(data)
