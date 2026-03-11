# Pico root boot.py
# Ensure shared core and app folders are importable at startup.
import sys

for p in ("/Core", "/apps/guild_sim", "/apps/sw_digital", "/apps/open_vpet"):
    if p not in sys.path:
        sys.path.append(p)

try:
    from hardware_runtime import get_profile_name, get_profile

    pname = get_profile_name()
    p = get_profile()
    print("boot.py: profile={} board={} display={}".format(pname, p.get("board", "?"), p.get("display", "?")))
except Exception:
    pass

print("boot.py: paths ready")
