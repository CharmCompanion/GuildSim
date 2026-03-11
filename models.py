import json
import os
import random
import time
import math


def _path_join(a, b):
    if a.endswith("/"):
        return a + b
    return a + "/" + b


def _path_exists(path):
    try:
        os.stat(path)
        return True
    except OSError:
        return False


def _ensure_dir(path):
    try:
        os.mkdir(path)
    except OSError:
        pass


def _sample_without_replacement(items, count):
    # MicroPython may not provide random.sample; this keeps behavior equivalent.
    src = list(items)
    out = []
    take = min(len(src), count)
    for _ in range(take):
        idx = random.randint(0, len(src) - 1)
        out.append(src.pop(idx))
    return out

RACE_OPTIONS = ["Human", "Elf", "Dwarf", "Beastkin", "Undead", "Goblin", "Dragonborn"]

PERSONALITY_TRAITS = [
    "Brave", "Cautious", "Greedy", "Loyal", "Reckless",
    "Cunning", "Kind", "Stubborn", "Curious", "Lazy"
]

BASE_NAMES = [
    "Aldric", "Brynn", "Cedric", "Dahlia", "Eirik", "Freya",
    "Gareth", "Hilda", "Ingrid", "Jareth", "Kira", "Lyra",
    "Magnus", "Nessa", "Orin", "Petra", "Quinn", "Rowan",
    "Sigrid", "Theron", "Ulric", "Vera", "Wren", "Xara",
    "Ymir", "Zara", "Ash", "Bram", "Cleo", "Dax",
    "Ember", "Flint", "Gale", "Hex", "Ivy", "Jett",
    "Knox", "Luna", "Moss", "Nyx", "Pike", "Reed",
    "Sage", "Thorn", "Vale", "Wolf", "Rook", "Sable"
]

CLASS_DEFINITIONS = {
    "Recruit": {
        "description": "A fresh adventurer with no specialization.",
        "requirements": {},
        "cost": 0,
        "stat_bonuses": {}
    },
    "Warrior": {
        "description": "A melee combat specialist.",
        "requirements": {"melee_xp": 50},
        "cost": 100,
        "stat_bonuses": {"STR": 3, "VIT": 2}
    },
    "Knight": {
        "description": "An armored defender of the guild.",
        "requirements": {"melee_xp": 120, "passive_xp": 40},
        "cost": 250,
        "stat_bonuses": {"STR": 2, "VIT": 5, "DEF": 3}
    },
    "Mage": {
        "description": "A wielder of arcane magic.",
        "requirements": {"magic_xp": 50},
        "cost": 100,
        "stat_bonuses": {"INT": 3, "MP": 10}
    },
    "Ranger": {
        "description": "A ranged combat expert and scout.",
        "requirements": {"range_xp": 50},
        "cost": 100,
        "stat_bonuses": {"DEX": 3, "SPD": 2}
    },
    "Paladin": {
        "description": "Holy warrior combining melee and magic.",
        "requirements": {"melee_xp": 100, "magic_xp": 60},
        "cost": 400,
        "stat_bonuses": {"STR": 3, "INT": 2, "VIT": 3}
    },
    "Assassin": {
        "description": "Master of stealth and critical strikes.",
        "requirements": {"range_xp": 80, "melee_xp": 40},
        "cost": 350,
        "stat_bonuses": {"DEX": 4, "SPD": 3, "STR": 1}
    },
    "Necromancer": {
        "description": "Dark mage who commands the undead.",
        "requirements": {"magic_xp": 120},
        "cost": 500,
        "stat_bonuses": {"INT": 5, "MP": 15}
    }
}

SKILL_CATALOG = {
    "Slash": {"category": "melee", "rank": 1, "cost": 20, "power": 8, "description": "Basic sword strike"},
    "Heavy Strike": {"category": "melee", "rank": 2, "cost": 60, "power": 18, "description": "Powerful overhead blow"},
    "Whirlwind": {"category": "melee", "rank": 3, "cost": 150, "power": 30, "description": "Spinning attack hitting all foes"},
    "Shield Bash": {"category": "melee", "rank": 2, "cost": 80, "power": 12, "description": "Stun enemy with shield"},
    "Fireball": {"category": "magic", "rank": 1, "cost": 25, "power": 10, "description": "Launch a ball of fire"},
    "Heal": {"category": "magic", "rank": 1, "cost": 30, "power": 0, "description": "Restore ally HP"},
    "Lightning": {"category": "magic", "rank": 2, "cost": 80, "power": 22, "description": "Call down lightning"},
    "Barrier": {"category": "magic", "rank": 2, "cost": 70, "power": 0, "description": "Create a protective shield"},
    "Meteor": {"category": "magic", "rank": 3, "cost": 200, "power": 40, "description": "Rain destruction from above"},
    "Quick Shot": {"category": "range", "rank": 1, "cost": 20, "power": 7, "description": "Fast arrow shot"},
    "Aimed Shot": {"category": "range", "rank": 2, "cost": 65, "power": 20, "description": "Precise critical shot"},
    "Barrage": {"category": "range", "rank": 3, "cost": 160, "power": 28, "description": "Volley of arrows"},
    "Trap": {"category": "range", "rank": 2, "cost": 50, "power": 10, "description": "Set a trap for enemies"},
    "War Cry": {"category": "passive", "rank": 1, "cost": 30, "power": 0, "description": "Boost party morale"},
    "Iron Will": {"category": "passive", "rank": 2, "cost": 80, "power": 0, "description": "Resist status effects"},
    "Leadership": {"category": "passive", "rank": 3, "cost": 180, "power": 0, "description": "Boost entire party stats"},
}

MISSION_TEMPLATES = [
    {"name": "Goblin Cave Raid", "difficulty": 1, "gold_reward": 50, "xp_reward": 20, "duration": 30,
     "description": "Clear out a small goblin nest nearby."},
    {"name": "Escort the Merchant", "difficulty": 1, "gold_reward": 40, "xp_reward": 15, "duration": 25,
     "description": "Protect a merchant on the road to town."},
    {"name": "Lost Relic Recovery", "difficulty": 2, "gold_reward": 100, "xp_reward": 40, "duration": 60,
     "description": "Retrieve a stolen artifact from bandits."},
    {"name": "Haunted Crypt", "difficulty": 2, "gold_reward": 120, "xp_reward": 50, "duration": 45,
     "description": "Investigate strange happenings in the old crypt."},
    {"name": "Dragon's Outpost", "difficulty": 3, "gold_reward": 250, "xp_reward": 100, "duration": 90,
     "description": "Assault a dragon's forward outpost."},
    {"name": "Wyvern Hunt", "difficulty": 3, "gold_reward": 200, "xp_reward": 80, "duration": 75,
     "description": "Hunt a wyvern terrorizing the countryside."},
    {"name": "Demon Gate", "difficulty": 4, "gold_reward": 500, "xp_reward": 200, "duration": 120,
     "description": "Close a portal leaking demonic creatures."},
    {"name": "Shadow Lord's Keep", "difficulty": 5, "gold_reward": 1000, "xp_reward": 400, "duration": 180,
     "description": "Storm the fortress of the Shadow Lord himself."},
    {"name": "Herb Gathering", "difficulty": 1, "gold_reward": 25, "xp_reward": 10, "duration": 15,
     "description": "Collect medicinal herbs from the forest."},
    {"name": "Bandit Ambush", "difficulty": 2, "gold_reward": 90, "xp_reward": 35, "duration": 40,
     "description": "Intercept a bandit raiding party."},
    {"name": "Undead Siege", "difficulty": 3, "gold_reward": 180, "xp_reward": 70, "duration": 60,
     "description": "Defend a village from waves of undead."},
    {"name": "Ancient Dungeon", "difficulty": 4, "gold_reward": 400, "xp_reward": 150, "duration": 100,
     "description": "Explore the depths of a forgotten dungeon."},
]

ADVENTURE_BASES = ["Warrior", "Mage", "Ranger", "Rogue", "Paladin", "Necromancer", "Cleric", "Monk"]
ADVENTURE_ADDON_PARTS = {
    "hair": ["Short", "Long", "Braids", "Spikes", "Ponytail", "Bald", "Crown", "Hood"],
    "face": ["Scar", "Mask", "Paint", "Tattoo", "Eyepatch", "Beard", "Glasses", "None"],
    "outfit": ["Leather", "Plate", "Robe", "Cloak", "Rags", "Royal", "Shadow", "Hunter"],
}

ADVENTURE_PREFIX = [
    "Crimson", "Ashen", "Twilight", "Storm", "Ivory", "Umbral", "Starfall", "Iron", "Frost", "Emerald", "Sable", "Radiant",
]
ADVENTURE_SUFFIX = [
    "Expedition", "Run", "Siege", "Path", "Incursion", "Delve", "Hunt", "Trial", "Venture", "Crossing", "Skirmish", "Operation",
]


def _hash_text(s):
    h = 2166136261
    for ch in s:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def _b36_encode(n):
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if n <= 0:
        return "0"
    out = ""
    while n > 0:
        n, r = divmod(n, 36)
        out = chars[r] + out
    return out


def _b36_decode(s):
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    idx = {}
    for i, c in enumerate(chars):
        idx[c] = i
    n = 0
    for ch in s.upper():
        n = n * 36 + idx.get(ch, 0)
    return n


def _seed_checksum(core):
    return _b36_encode(_hash_text(core) % (36 * 36)).rjust(2, "0")


def build_adventure_seed_code(adventure_stats, character_parts=None):
    stats = adventure_stats or {}
    parts = character_parts or {}

    difficulty = max(1, min(9, int(stats.get("difficulty", 1))))
    gold = max(0, min(9999, int(stats.get("gold_reward", 50))))
    xp = max(0, min(9999, int(stats.get("xp_reward", 20))))
    duration = max(1, min(999, int(stats.get("duration", 30))))
    variant = max(0, min(9999, int(stats.get("variant", 0))))

    base_idx = max(0, min(len(ADVENTURE_BASES) - 1, int(parts.get("base_idx", 0))))
    hair_idx = max(0, min(len(ADVENTURE_ADDON_PARTS["hair"]) - 1, int(parts.get("hair_idx", 0))))
    face_idx = max(0, min(len(ADVENTURE_ADDON_PARTS["face"]) - 1, int(parts.get("face_idx", 0))))
    outfit_idx = max(0, min(len(ADVENTURE_ADDON_PARTS["outfit"]) - 1, int(parts.get("outfit_idx", 0))))

    n = difficulty
    n = n * 10000 + gold
    n = n * 10000 + xp
    n = n * 1000 + duration
    n = n * 8 + base_idx
    n = n * 8 + hair_idx
    n = n * 8 + face_idx
    n = n * 8 + outfit_idx
    n = n * 10000 + variant

    core = _b36_encode(n)
    return "ADV-" + core + _seed_checksum(core)


def decode_adventure_seed_code(seed_code):
    if not seed_code:
        return None
    s = str(seed_code).strip().upper().replace(" ", "")
    if s.startswith("ADV-"):
        s = s[4:]
    if len(s) < 3:
        return None

    core = s[:-2]
    chk = s[-2:]
    if _seed_checksum(core) != chk:
        return None

    n = _b36_decode(core)
    variant = n % 10000
    n //= 10000
    outfit_idx = n % 8
    n //= 8
    face_idx = n % 8
    n //= 8
    hair_idx = n % 8
    n //= 8
    base_idx = n % 8
    n //= 8
    duration = n % 1000
    n //= 1000
    xp = n % 10000
    n //= 10000
    gold = n % 10000
    n //= 10000
    difficulty = max(1, n)

    name = ADVENTURE_PREFIX[variant % len(ADVENTURE_PREFIX)] + " " + ADVENTURE_SUFFIX[(variant // 7) % len(ADVENTURE_SUFFIX)]
    return {
        "name": name,
        "difficulty": difficulty,
        "gold_reward": gold,
        "xp_reward": xp,
        "duration": duration,
        "description": "Seeded adventure generated from shared code.",
        "seed_code": "ADV-" + core + chk,
        "character_seed": {
            "base": ADVENTURE_BASES[base_idx],
            "hair": ADVENTURE_ADDON_PARTS["hair"][hair_idx],
            "face": ADVENTURE_ADDON_PARTS["face"][face_idx],
            "outfit": ADVENTURE_ADDON_PARTS["outfit"][outfit_idx],
            "base_idx": base_idx,
            "hair_idx": hair_idx,
            "face_idx": face_idx,
            "outfit_idx": outfit_idx,
        },
        "variant": variant,
    }


def mission_with_seed(mission):
    m = dict(mission)
    if m.get("seed_code"):
        return m

    variant = _hash_text(m.get("name", "mission")) % 10000
    parts = {"base_idx": variant % 8, "hair_idx": (variant // 3) % 8, "face_idx": (variant // 5) % 8, "outfit_idx": (variant // 7) % 8}
    code = build_adventure_seed_code(
        {
            "difficulty": m.get("difficulty", 1),
            "gold_reward": m.get("gold_reward", 50),
            "xp_reward": m.get("xp_reward", 20),
            "duration": m.get("duration", 30),
            "variant": variant,
        },
        parts,
    )
    m["seed_code"] = code
    m["character_seed"] = {
        "base": ADVENTURE_BASES[parts["base_idx"]],
        "hair": ADVENTURE_ADDON_PARTS["hair"][parts["hair_idx"]],
        "face": ADVENTURE_ADDON_PARTS["face"][parts["face_idx"]],
        "outfit": ADVENTURE_ADDON_PARTS["outfit"][parts["outfit_idx"]],
    }
    return m

CATEGORY_UNLOCK_GATES = {
    "melee": {"gold": 0, "guild_rank": 0, "total_xp": 0},
    "magic": {"gold": 100, "guild_rank": 2, "total_xp": 50},
    "range": {"gold": 100, "guild_rank": 2, "total_xp": 50},
    "passive": {"gold": 200, "guild_rank": 3, "total_xp": 150},
}


def generate_recruit(guild_rank=1):
    name = random.choice(BASE_NAMES)
    race = random.choice(RACE_OPTIONS)
    personality = random.choice(PERSONALITY_TRAITS)

    base_stat = 5 + guild_rank
    stats = {
        "HP": random.randint(base_stat * 3, base_stat * 5),
        "MP": random.randint(base_stat, base_stat * 3),
        "STR": random.randint(base_stat - 2, base_stat + 3),
        "INT": random.randint(base_stat - 2, base_stat + 3),
        "DEX": random.randint(base_stat - 2, base_stat + 3),
        "VIT": random.randint(base_stat - 2, base_stat + 3),
        "SPD": random.randint(base_stat - 2, base_stat + 3),
        "DEF": random.randint(base_stat - 2, base_stat + 3),
    }

    affinity_options = ["melee", "magic", "range"]
    affinity = random.choice(affinity_options)

    recruit = {
        "id": f"r_{int(time.time() * 1000)}_{random.randint(100, 999)}",
        "name": name,
        "race": race,
        "personality": personality,
        "job_class": "Recruit",
        "level": 1,
        "xp": 0,
        "xp_to_next": 100,
        "stats": stats,
        "current_hp": stats["HP"],
        "current_mp": stats["MP"],
        "affinity": affinity,
        "training_xp": {"melee": 0, "magic": 0, "range": 0, "passive": 0},
        "skills": [],
        "fatigue": 0,
        "injury_timer": 0,
        "morale": 80,
        "is_active": False,
        "hire_cost": 30 + (guild_rank * 10) + random.randint(-10, 20),
        "recruited_at": None,
    }
    return recruit


def compute_power(recruit):
    s = recruit["stats"]
    level_bonus = recruit["level"] * 2
    skill_bonus = len(recruit.get("skills", [])) * 3
    stat_total = s["STR"] + s["INT"] + s["DEX"] + s["VIT"] + s["SPD"] + s["DEF"]
    return stat_total + level_bonus + skill_bonus


def compute_party_power(party_members):
    total = sum(compute_power(m) for m in party_members)
    synergy = len(party_members) * 5
    return total + synergy


def check_level_up(recruit):
    leveled = False
    while recruit["xp"] >= recruit["xp_to_next"]:
        recruit["xp"] -= recruit["xp_to_next"]
        recruit["level"] += 1
        recruit["xp_to_next"] = int(recruit["xp_to_next"] * 1.3)
        for stat in recruit["stats"]:
            recruit["stats"][stat] += random.randint(1, 3)
        recruit["current_hp"] = recruit["stats"]["HP"]
        recruit["current_mp"] = recruit["stats"]["MP"]
        leveled = True
    return leveled


def apply_training(recruit, category, intensity=1):
    xp_gain = 10 * intensity + random.randint(1, 5)
    recruit["training_xp"][category] += xp_gain

    stat_map = {
        "melee": ["STR", "VIT"],
        "magic": ["INT", "MP"],
        "range": ["DEX", "SPD"],
        "passive": ["VIT", "DEF"],
    }

    for stat in stat_map.get(category, []):
        recruit["stats"][stat] += random.randint(0, intensity)

    recruit["xp"] += xp_gain // 2
    recruit["fatigue"] += 5 * intensity + random.randint(0, 3)
    recruit["morale"] = max(0, recruit["morale"] - random.randint(0, 2))

    check_level_up(recruit)
    return xp_gain


def get_available_classes(recruit):
    available = []
    for cls_name, cls_def in CLASS_DEFINITIONS.items():
        if cls_name == recruit["job_class"]:
            continue
        if cls_name == "Recruit":
            continue
        met = True
        for req_key, req_val in cls_def["requirements"].items():
            if recruit["training_xp"].get(req_key.replace("_xp", ""), 0) < req_val:
                met = False
                break
        if met:
            available.append(cls_name)
    return available


def promote_class(recruit, class_name):
    if class_name not in CLASS_DEFINITIONS:
        return False, "Unknown class"
    cls = CLASS_DEFINITIONS[class_name]
    for stat, bonus in cls["stat_bonuses"].items():
        if stat in recruit["stats"]:
            recruit["stats"][stat] += bonus
    recruit["job_class"] = class_name
    recruit["current_hp"] = recruit["stats"]["HP"]
    recruit["current_mp"] = recruit["stats"]["MP"]
    return True, f"Promoted to {class_name}!"


def can_learn_skill(recruit, skill_name):
    if skill_name in recruit.get("skills", []):
        return False, "Already learned"
    if skill_name not in SKILL_CATALOG:
        return False, "Unknown skill"
    skill = SKILL_CATALOG[skill_name]
    cat = skill["category"]
    rank = skill["rank"]
    txp = recruit["training_xp"].get(cat, 0)
    if rank == 2 and txp < 30:
        return False, f"Need {cat} training XP >= 30"
    if rank == 3 and txp < 80:
        return False, f"Need {cat} training XP >= 80"
    return True, "Can learn"


def learn_skill(recruit, skill_name):
    can, msg = can_learn_skill(recruit, skill_name)
    if not can:
        return False, msg
    skill = SKILL_CATALOG[skill_name]
    cost = skill["cost"]
    if recruit.get("affinity") == skill["category"]:
        cost = int(cost * 0.8)
    recruit.setdefault("skills", []).append(skill_name)
    return True, f"Learned {skill_name}! (Cost: {cost}g)"


def run_mission(party, mission_template, guild):
    mission = dict(mission_template)
    party_power = compute_party_power(party)
    difficulty_threshold = mission["difficulty"] * 30

    success_chance = min(95, max(10, 50 + (party_power - difficulty_threshold)))
    roll = random.randint(1, 100)
    success = roll <= success_chance

    log_lines = []
    log_lines.append(f"=== Mission: {mission['name']} ===")
    log_lines.append(f"Party Power: {party_power} vs Difficulty: {difficulty_threshold}")
    log_lines.append(f"Success Chance: {success_chance}% | Roll: {roll}")

    if success:
        gold_earned = mission["gold_reward"] + random.randint(-10, 20)
        xp_earned = mission["xp_reward"]
        guild["gold"] += gold_earned
        guild["total_missions"] = guild.get("total_missions", 0) + 1
        guild["successful_missions"] = guild.get("successful_missions", 0) + 1
        log_lines.append(f"SUCCESS! Earned {gold_earned}g")

        for member in party:
            member_xp = xp_earned + random.randint(0, 10)
            member["xp"] += member_xp
            member["fatigue"] += random.randint(5, 15)
            member["morale"] = min(100, member["morale"] + random.randint(2, 8))
            leveled = check_level_up(member)
            log_lines.append(f"  {member['name']}: +{member_xp} XP" + (" [LEVEL UP!]" if leveled else ""))

        if random.random() < 0.15 * mission["difficulty"]:
            soul_gems = random.randint(1, mission["difficulty"])
            guild["soul_gems"] = guild.get("soul_gems", 0) + soul_gems
            log_lines.append(f"  Found {soul_gems} Soul Gem(s)!")
    else:
        guild["total_missions"] = guild.get("total_missions", 0) + 1
        log_lines.append("FAILED!")

        for member in party:
            member["fatigue"] += random.randint(10, 25)
            member["morale"] = max(0, member["morale"] - random.randint(5, 15))
            if random.random() < 0.3:
                damage = random.randint(5, 20)
                member["current_hp"] = max(1, member["current_hp"] - damage)
                member["injury_timer"] = random.randint(30, 90)
                log_lines.append(f"  {member['name']} was injured! (-{damage} HP, recovering...)")
            else:
                member["xp"] += mission["xp_reward"] // 4
                log_lines.append(f"  {member['name']}: +{mission['xp_reward'] // 4} XP (consolation)")

    return success, log_lines


def tick_update(guild, roster):
    for recruit in roster:
        if not recruit.get("is_active"):
            continue
        if recruit["current_hp"] < recruit["stats"]["HP"]:
            recruit["current_hp"] = min(recruit["stats"]["HP"], recruit["current_hp"] + 1)
        if recruit["current_mp"] < recruit["stats"]["MP"]:
            recruit["current_mp"] = min(recruit["stats"]["MP"], recruit["current_mp"] + 1)
        if recruit["fatigue"] > 0:
            recruit["fatigue"] = max(0, recruit["fatigue"] - 1)
        if recruit["injury_timer"] > 0:
            recruit["injury_timer"] = max(0, recruit["injury_timer"] - 1)
        if recruit["morale"] < 80 and recruit["fatigue"] < 20:
            recruit["morale"] = min(100, recruit["morale"] + 1)


def get_guild_rank_title(rank):
    titles = {
        1: "Bronze",
        2: "Silver",
        3: "Gold",
        4: "Platinum",
        5: "Diamond",
        6: "Mythril",
        7: "Adamantine",
        8: "Legendary",
        9: "Eternal",
        10: "Transcendent"
    }
    return titles.get(rank, f"Rank {rank}")


def check_guild_rank_up(guild):
    rank = guild.get("rank", 1)
    missions = guild.get("successful_missions", 0)
    thresholds = {1: 3, 2: 8, 3: 15, 4: 25, 5: 40, 6: 60, 7: 85, 8: 120, 9: 200}
    needed = thresholds.get(rank, 999)
    if missions >= needed and rank < 10:
        guild["rank"] = rank + 1
        return True, f"Guild ranked up to {get_guild_rank_title(rank + 1)}!"
    return False, None


def default_guild(name="New Guild", lord_name="Guild Master"):
    return {
        "name": name,
        "lord_name": lord_name,
        "rank": 1,
        "gold": 200,
        "soul_gems": 0,
        "total_missions": 0,
        "successful_missions": 0,
        "created_at": time.time(),
        "last_tick": time.time(),
        "unlocked_categories": ["melee"],
        "mission_log": [],
        "custom_adventure_seeds": [],
    }


def save_game(slot, guild, roster):
    slot_dir = f"saves/{slot}"
    _ensure_dir("saves")
    _ensure_dir(slot_dir)
    with open(_path_join(slot_dir, "guild.json"), "w") as f:
        json.dump(guild, f, indent=2)
    with open(_path_join(slot_dir, "roster.json"), "w") as f:
        json.dump(roster, f, indent=2)


def load_game(slot):
    slot_dir = f"saves/{slot}"
    guild_path = _path_join(slot_dir, "guild.json")
    roster_path = _path_join(slot_dir, "roster.json")
    if not _path_exists(guild_path):
        return None, None
    with open(guild_path, "r") as f:
        guild = json.load(f)
    roster = []
    if _path_exists(roster_path):
        with open(roster_path, "r") as f:
            roster = json.load(f)
    return guild, roster


def get_slot_info(slot):
    guild, roster = load_game(slot)
    if guild is None:
        return None
    return {
        "guild_name": guild["name"],
        "lord_name": guild["lord_name"],
        "rank": guild["rank"],
        "rank_title": get_guild_rank_title(guild["rank"]),
        "gold": guild["gold"],
        "roster_size": len(roster),
        "active_count": sum(1 for r in roster if r.get("is_active")),
    }


def delete_save(slot):
    slot_dir = f"saves/{slot}"
    guild_path = _path_join(slot_dir, "guild.json")
    roster_path = _path_join(slot_dir, "roster.json")
    if _path_exists(guild_path):
        os.remove(guild_path)
    if _path_exists(roster_path):
        os.remove(roster_path)


def seed_recruit_pool(guild_rank, count=4):
    pool = []
    for _ in range(count):
        pool.append(generate_recruit(guild_rank))
    return pool


def get_available_missions(guild_rank, custom_seed_codes=None):
    custom = custom_seed_codes or []
    out = []
    for code in custom:
        m = decode_adventure_seed_code(code)
        if m and m.get("difficulty", 1) <= min(guild_rank + 1, 9):
            out.append(mission_with_seed(m))

    available = [m for m in MISSION_TEMPLATES if m["difficulty"] <= min(guild_rank + 1, 5)]
    sampled = _sample_without_replacement(available, max(0, 4 - len(out)))
    for m in sampled:
        out.append(mission_with_seed(m))

    return out[:4]


def compute_total_roster_xp(roster):
    total = 0
    for r in roster:
        for cat_xp in r.get("training_xp", {}).values():
            total += cat_xp
    return total


def check_category_unlock(guild, category, roster=None):
    gate = CATEGORY_UNLOCK_GATES.get(category)
    if not gate:
        return False, "Unknown category"
    if guild["gold"] < gate["gold"]:
        return False, f"Need {gate['gold']}g (have {guild['gold']}g)"
    if guild["rank"] < gate["guild_rank"]:
        return False, f"Need Guild Rank {gate['guild_rank']}"
    if roster is not None and gate["total_xp"] > 0:
        total_xp = compute_total_roster_xp(roster)
        if total_xp < gate["total_xp"]:
            return False, f"Need {gate['total_xp']} total roster XP (have {total_xp})"
    return True, "Can unlock"


def unlock_category(guild, category, roster=None):
    can, msg = check_category_unlock(guild, category, roster)
    if not can:
        return False, msg
    gate = CATEGORY_UNLOCK_GATES[category]
    guild["gold"] -= gate["gold"]
    if category not in guild.get("unlocked_categories", []):
        guild.setdefault("unlocked_categories", []).append(category)
    return True, f"Unlocked {category} training!"
