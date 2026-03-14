"""Unified skill catalog imported from Refs/Skills-main/Gravebound_Skill_Reference.md."""

SKILLS = [
    {"name": "Rapid Recovery", "rank": "S", "cost": 75000, "category": "Combat", "effect": "Regenerate health at 100x natural rate.", "locked": False},
    {"name": "Bladestorm", "rank": "A", "cost": 40000, "category": "Combat", "effect": "Whirlwind strike that hits nearby enemies.", "locked": False},
    {"name": "Combat Precognition", "rank": "A", "cost": 35000, "category": "Combat", "effect": "Perceive enemy intent moments ahead.", "locked": False},
    {"name": "Limitless Growth", "rank": "B", "cost": 15000, "category": "Combat", "effect": "Remove level and stat growth caps.", "locked": False},
    {"name": "High-Speed Strike", "rank": "B", "cost": 10000, "category": "Combat", "effect": "Triple attack speed for burst window.", "locked": False},
    {"name": "Martial Arts", "rank": "C", "cost": 2500, "category": "Combat", "effect": "Advanced unarmed combat proficiency.", "locked": False},
    {"name": "Iron Body", "rank": "C", "cost": 1500, "category": "Combat", "effect": "Reduce incoming physical damage.", "locked": False},
    {"name": "Weapon Mastery", "rank": "D", "cost": 400, "category": "Combat", "effect": "Baseline proficiency with all weapons.", "locked": False},
    {"name": "Quick Reflexes", "rank": "D", "cost": 250, "category": "Combat", "effect": "Improve dodge timing and reactions.", "locked": False},
    {"name": "Immersion", "rank": "S", "cost": 75000, "category": "Magic", "effect": "Phase through solid matter.", "locked": False},
    {"name": "Spell Weaver", "rank": "A", "cost": 50000, "category": "Magic", "effect": "Compose new spells from mana threads.", "locked": False},
    {"name": "Mana Overflow", "rank": "A", "cost": 30000, "category": "Magic", "effect": "Exceed safe mana limits for burst output.", "locked": False},
    {"name": "High-Speed Incantation", "rank": "B", "cost": 12000, "category": "Magic", "effect": "Near-instant casting speed.", "locked": False},
    {"name": "Elemental Affinity", "rank": "B", "cost": 8000, "category": "Magic", "effect": "Attune to all elemental domains.", "locked": False},
    {"name": "Thread Control", "rank": "C", "cost": 3000, "category": "Magic", "effect": "Control and disrupt mana threads.", "locked": False},
    {"name": "Mana Sense", "rank": "C", "cost": 1200, "category": "Magic", "effect": "Perceive magical signatures.", "locked": False},
    {"name": "Minor Enchantment", "rank": "D", "cost": 350, "category": "Magic", "effect": "Temporary weak enchantments on items.", "locked": False},
    {"name": "Mana Shield", "rank": "D", "cost": 200, "category": "Magic", "effect": "Small defensive mana barrier.", "locked": False},
    {"name": "Probability Manipulation", "rank": "S", "cost": 75000, "category": "Utility", "effect": "Nudge event outcomes in your favor.", "locked": True},
    {"name": "Parallel Minds", "rank": "A", "cost": 45000, "category": "Utility", "effect": "Dual-track thought processing.", "locked": False},
    {"name": "Shadow Step", "rank": "A", "cost": 28000, "category": "Utility", "effect": "Line-of-sight short teleport.", "locked": False},
    {"name": "Spatial Storage", "rank": "B", "cost": 10000, "category": "Utility", "effect": "Personal dimensional inventory.", "locked": False},
    {"name": "Language of All", "rank": "B", "cost": 6000, "category": "Utility", "effect": "Understand all spoken/written languages.", "locked": False},
    {"name": "Appraisal", "rank": "C", "cost": 2000, "category": "Utility", "effect": "Inspect entities for stats and state.", "locked": False},
    {"name": "Lockpicking", "rank": "C", "cost": 1000, "category": "Utility", "effect": "Open mechanical locks without tools.", "locked": False},
    {"name": "Playing Dead", "rank": "D", "cost": 500, "category": "Utility", "effect": "Undetectable metabolic stillness.", "locked": False},
    {"name": "Minor Disguise", "rank": "D", "cost": 150, "category": "Utility", "effect": "Temporary facial/voice disguise.", "locked": False},
    {"name": "Immortal Physique", "rank": "S", "cost": 75000, "category": "Passive", "effect": "Reconstitute after lethal damage.", "locked": True},
    {"name": "Soul Sight", "rank": "A", "cost": 35000, "category": "Passive", "effect": "Perceive soul strength and nature.", "locked": False},
    {"name": "Danger Premonition", "rank": "A", "cost": 25000, "category": "Passive", "effect": "Sense lethal threats early.", "locked": False},
    {"name": "Adaptive Body", "rank": "B", "cost": 12000, "category": "Passive", "effect": "Biological adaptation to repeated stress.", "locked": False},
    {"name": "Mental Fortress", "rank": "B", "cost": 7000, "category": "Passive", "effect": "Immunity to mental control and illusions.", "locked": False},
    {"name": "Pain Tolerance", "rank": "C", "cost": 2500, "category": "Passive", "effect": "Reduce combat impairment from pain.", "locked": False},
    {"name": "Enhanced Senses", "rank": "C", "cost": 1500, "category": "Passive", "effect": "Enhanced hearing, sight, and smell.", "locked": False},
    {"name": "Lucky Aura", "rank": "D", "cost": 450, "category": "Passive", "effect": "Small passive luck increase.", "locked": False},
    {"name": "Toughness", "rank": "D", "cost": 200, "category": "Passive", "effect": "Permanent max HP increase.", "locked": False},
]


def all_skills():
    return SKILLS


def find_skill(name):
    needle = name.strip().lower()
    for skill in SKILLS:
        if skill["name"].lower() == needle:
            return skill
    return None


def category_summary():
    out = {}
    for skill in SKILLS:
        cat = skill["category"]
        out[cat] = out.get(cat, 0) + 1
    return out
