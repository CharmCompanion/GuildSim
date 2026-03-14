"""Guild progression and equipment restrictions."""

CATEGORY_UNLOCK_RULES = {
    "Magic": {"gold": 5000, "guild_level": 2, "roster_xp": 100},
    "Range": {"gold": 8000, "guild_level": 2, "roster_xp": 150},
    "Passive": {"gold": 12000, "guild_level": 3, "roster_xp": 220},
}


WEAPON_ARMOR_RULES = {
    "sword": ["light", "medium", "heavy"],
    "staff": ["light", "medium"],
    "bow": ["light", "medium"],
}


def roster_xp_total(roster):
    return sum(int(r.get("xp", 0)) for r in roster.get("recruits", []))


def try_unlock_category(guild, roster, category):
    if category in guild.get("unlocked_categories", []):
        return False, "already-unlocked"
    if category not in CATEGORY_UNLOCK_RULES:
        return False, "unknown-category"

    rule = CATEGORY_UNLOCK_RULES[category]
    if guild.get("gold", 0) < rule["gold"]:
        return False, "gold-too-low"
    if guild.get("rank", 0) < rule["guild_level"]:
        return False, "rank-too-low"
    if roster_xp_total(roster) < rule["roster_xp"]:
        return False, "roster-xp-too-low"

    guild["gold"] -= rule["gold"]
    guild.setdefault("unlocked_categories", []).append(category)
    return True, "unlocked"


def can_use_armor(weapon_type, armor_weight):
    allowed = WEAPON_ARMOR_RULES.get(weapon_type, ["light"])
    return armor_weight in allowed


def blocked_skill_categories(weapon_type, armor_weight):
    # Heavy armor disables higher-tier magic behavior.
    blocked = []
    if armor_weight == "heavy":
        blocked.append("Magic")
    if not can_use_armor(weapon_type, armor_weight):
        blocked.extend(["Magic", "Range"])
    return blocked
