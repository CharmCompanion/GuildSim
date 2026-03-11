"""Seed utility for guild naming, recruit pools, and SW2.5 campaign templates.

No town generation is performed.
"""

import random

from game_paths import SW25_CAMPAIGNS_DIR
from roster_manager import add_recruit, new_recruit
from storage import save_json


FIRST_NAMES = [
    "Aren",
    "Mira",
    "Tor",
    "Selene",
    "Bran",
    "Kael",
    "Rin",
    "Luca",
    "Iris",
    "Nox",
]

LAST_NAMES = [
    "Stone",
    "Vale",
    "Drake",
    "Hallow",
    "Frost",
    "Dawn",
    "Kerr",
    "Voss",
    "Ash",
    "Moor",
]

AFFINITIES = ["Combat", "Magic", "Utility", "Passive"]


def random_recruit_name():
    return "{} {}".format(random.choice(FIRST_NAMES), random.choice(LAST_NAMES))


def rename_guild(guild, guild_name=None, lord_name=None):
    if guild_name:
        guild["guild_name"] = guild_name.strip()
    if lord_name:
        guild["lord"] = lord_name.strip()


def seed_recruit_pool(roster, count=5):
    added = 0
    for _ in range(max(0, int(count))):
        recruit = new_recruit(random_recruit_name(), random.choice(AFFINITIES))
        ok, _reason = add_recruit(roster, recruit)
        if ok:
            added += 1
    return added


def seed_campaign_templates(count=3):
    created = []
    templates = [
        ("bandit_road", "Bandit Road", 9),
        ("ruined_watchtower", "Ruined Watchtower", 10),
        ("ashen_catacomb", "Ashen Catacomb", 11),
        ("sunken_archive", "Sunken Archive", 12),
        ("wyrm_ridge", "Wyrm Ridge", 13),
    ]

    for idx in range(min(max(0, int(count)), len(templates))):
        slug, title, tn = templates[idx]
        rel = SW25_CAMPAIGNS_DIR + "/" + slug + ".json"
        save_json(
            rel,
            {
                "title": title,
                "target_number": tn,
                "notes": "Seeded template campaign.",
            },
        )
        created.append(rel)

    return created
