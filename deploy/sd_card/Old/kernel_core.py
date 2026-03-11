"""Shared micro-kernel services for launcher, storage diagnostics, and app handoff."""

import gc
import time

from hardware_runtime import get_profile_name, get_profile
from storage import get_data_root, ensure_dir


PATHS = {
    "game_core": "game_core",
    "manifest": "game_core/manifest.json",
    "collections": "collections",
    "collection_book": "collections/collection.json",
    "sw25": "sw25",
    "sw25_campaigns": "sw25/campaigns",
    "guild_sim": "guild_sim",
    "open_vpet": "open_vpet",
}


APPS = {}


def ensure_runtime_dirs():
    root = get_data_root()
    for rel_path in PATHS.values():
        if rel_path.endswith(".json"):
            continue
        ensure_dir(root + "/" + rel_path)
    return root


def memory_free_bytes():
    try:
        gc.collect()
        return gc.mem_free()
    except Exception:
        return -1


def detect_time_source():
    # Try NTP if available, then fallback to local RTC.
    try:
        import ntptime  # type: ignore

        try:
            ntptime.settime()
            return "ntp-synced"
        except Exception:
            return "ntp-unavailable"
    except Exception:
        return "rtc-local"


def boot_diagnostics():
    root = ensure_runtime_dirs()
    profile_name = get_profile_name()
    profile = get_profile()
    print("=" * 70)
    print("BOOT DIAGNOSTICS")
    print("=" * 70)
    print("Data root: {}".format(root))
    print("Hardware profile: {} ({})".format(profile_name, profile.get("board", "unknown")))
    print("Display: {}".format(profile.get("display", "unknown")))
    print("Storage: {}".format(profile.get("storage", "unknown")))
    print("Time source: {}".format(detect_time_source()))
    mem_free = memory_free_bytes()
    if mem_free >= 0:
        print("Free memory bytes: {}".format(mem_free))
    else:
        print("Free memory bytes: unavailable")
    print("Boot timestamp: {}".format(int(time.time())))
    print("=" * 70)


def register_app(key, label, runner):
    APPS[key] = {"label": label, "runner": runner}


def app_menu_items():
    items = []
    for key in sorted(APPS.keys()):
        app = APPS[key]
        items.append({"label": app["label"], "action": app["runner"]})
    return items
