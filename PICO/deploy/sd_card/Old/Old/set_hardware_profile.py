"""CLI helper to set active hardware profile."""

from hardware_runtime import set_profile, supported_profiles, get_profile_name


def main():
    print("Current profile:", get_profile_name())
    print("Supported profiles:")
    for name in supported_profiles():
        print("-", name)

    choice = input("Set profile to > ").strip()
    if not choice:
        print("No change.")
        return

    ok = set_profile(choice)
    if ok:
        print("Profile set to:", choice)
    else:
        print("Invalid profile name.")


if __name__ == "__main__":
    main()
