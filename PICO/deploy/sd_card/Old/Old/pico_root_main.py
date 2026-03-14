# Pico root main.py
# Startup app picker so REPL typing is not required each boot.
import sys

for p in ("/Core", "/apps/guild_sim", "/apps/sw_digital", "/apps/open_vpet"):
    if p not in sys.path:
        sys.path.append(p)


def run_script(path):
    g = {"__name__": "__main__"}
    with open(path, "r") as handle:
        code = handle.read()
    exec(code, g)


def picker_loop():
    while True:
        print("\n=== APP PICKER ===")
        print("1) apps/Guild Sim")
        print("2) apps/ SW Digital")
        print("3) apps/Open VPet")
        print("q) Quit to REPL")
        try:
            choice = input("Select app > ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nLeaving app picker.")
            break

        if choice == "1":
            run_script("/apps/guild_sim/main.py")
        elif choice == "2":
            run_script("/apps/sw_digital/main.py")
        elif choice == "3":
            run_script("/apps/open_vpet/main.py")
        elif choice in ("q", "quit", "exit"):
            print("Leaving app picker.")
            break
        else:
            print("Invalid selection.")


picker_loop()
