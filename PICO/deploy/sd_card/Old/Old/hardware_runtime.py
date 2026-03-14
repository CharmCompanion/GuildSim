"""Hardware profile loader and helpers."""

from hardware_profiles import PROFILES, DEFAULT_PROFILE
from storage import load_json, save_json


PROFILE_FILE = "game_core/hardware_profile.json"


def get_profile_name():
    data = load_json(PROFILE_FILE, {"profile": DEFAULT_PROFILE})
    profile = data.get("profile", DEFAULT_PROFILE)
    if profile not in PROFILES:
        profile = DEFAULT_PROFILE
    return profile


def get_profile():
    return PROFILES[get_profile_name()]


def set_profile(profile_name):
    if profile_name not in PROFILES:
        return False
    save_json(PROFILE_FILE, {"profile": profile_name})
    return True


def supported_profiles():
    return sorted(PROFILES.keys())
