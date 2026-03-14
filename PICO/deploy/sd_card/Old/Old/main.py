from pc_menu import Menu, read_command
from kernel_core import boot_diagnostics, register_app, app_menu_items
from game_paths import GUILD_FILE
from storage import load_json


def _launcher_identity():
    guild = load_json(
        GUILD_FILE,
        {
            "guild_name": "Guild",
            "lord": "Guild Master",
            "rank": 1,
            "gold": 0,
        },
    )
    return guild


def run_launcher():
    running = {"value": True}

    boot_diagnostics()
    guild = _launcher_identity()

    def start_sword_world():
        print("\nBooting Sword World 2.5 kernel...")
        import sw25_kernel

        sw25_kernel.run()

    def start_guild_sim():
        print("\nOpening Guild Sim app menu...")
        import guild_sim_kernel

        def choose_slot(prompt):
            statuses = guild_sim_kernel.list_slot_status()
            print("=" * 70)
            print(prompt)
            print("=" * 70)
            for idx, info in enumerate(statuses):
                print("{}. {} => {}".format(idx + 1, info["slot"], info["label"]))
            try:
                pick = int(input("Select slot number (1-3) > ").strip()) - 1
            except Exception:
                return None
            if pick < 0 or pick >= len(statuses):
                return None
            return statuses[pick]

        app_running = True
        app_menu = Menu(
            [
                {"label": "New Game", "action": lambda: None},
                {"label": "Continue", "action": lambda: None},
                {"label": "Quit", "action": lambda: None},
            ],
            title="apps/Guild Sim",
        )
        app_menu.display()
        while app_running:
            cmd = read_command()
            if cmd == "w":
                app_menu.move(-1)
                continue
            if cmd == "s":
                app_menu.move(1)
                continue
            if cmd == "q":
                break
            if cmd not in ("", "e", "enter"):
                print("Unknown command. Use w/s/enter/q.")
                continue

            selected = app_menu.selected_index
            if selected == 0:
                slot = choose_slot("New Game - choose slot")
                if not slot:
                    print("Invalid slot selection.")
                    continue
                guild_sim_kernel.run(slot_id=slot["slot"], new_game=True)
                app_menu.display()
            elif selected == 1:
                slot = choose_slot("Continue - choose slot")
                if not slot:
                    print("Invalid slot selection.")
                    continue
                if not slot["exists"]:
                    print("Selected slot is empty. Start New Game first.")
                    app_menu.display()
                    continue
                guild_sim_kernel.run(slot_id=slot["slot"], new_game=False)
                app_menu.display()
            else:
                app_running = False

        print("Leaving Guild Sim app menu.")

    def start_open_vpet():
        print("\nBooting Open VPet kernel...")
        import open_vpet_kernel

        open_vpet_kernel.run()

    register_app("sw25", "apps/ SW Digital", start_sword_world)
    register_app("guild", "apps/Guild Sim", start_guild_sim)
    register_app("open_vpet", "apps/Open VPet", start_open_vpet)

    def exit_launcher():
        running["value"] = False

    launcher = Menu(
        [
            {
                "label": lambda: "Guild:{} | Lord:{} | Rank:{} | Gold:{}".format(
                    guild.get("guild_name", "Guild"),
                    guild.get("lord", "Guild Master"),
                    guild.get("rank", 1),
                    guild.get("gold", 0),
                ),
                "action": lambda: None,
            }
        ]
        + app_menu_items()
        + [{"label": "Exit", "action": exit_launcher}],
        title="PICO BOOTSTRAPPER",
    )

    launcher.display()
    while running["value"]:
        cmd = read_command()
        if cmd == "w":
            launcher.move(-1)
        elif cmd == "s":
            launcher.move(1)
        elif cmd in ("", "e", "enter"):
            launcher.select()
            if running["value"]:
                launcher.display()
        elif cmd == "q":
            exit_launcher()
        else:
            print("Unknown command. Use w/s/enter/q.")


if __name__ == "__main__":
    run_launcher()
