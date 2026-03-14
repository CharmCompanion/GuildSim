"""Real-time watch logic for injuries and equipment fatigue."""

import time


def tick_recruit(recruit, now_ts=None):
    now_ts = int(now_ts or time.time())

    # Passive vitality recovery per pulse.
    recruit.setdefault("stats", {}).setdefault("VIT", 0)
    recruit["stats"]["VIT"] += 1

    # Equipment fatigue accumulates over time and usage.
    recruit["equipment_fatigue"] = int(recruit.get("equipment_fatigue", 0)) + 1

    # Injury recovery check.
    injury_until = int(recruit.get("injury_until", 0))
    if injury_until and now_ts >= injury_until:
        recruit["injury_until"] = 0


def apply_mission_attrition(recruit, mission_difficulty=1):
    now_ts = int(time.time())
    fatigue_gain = max(1, int(mission_difficulty)) * 5
    recruit["equipment_fatigue"] = int(recruit.get("equipment_fatigue", 0)) + fatigue_gain

    # Chance of short injury timer.
    if mission_difficulty >= 2:
        recruit["injury_until"] = now_ts + 60 * mission_difficulty
