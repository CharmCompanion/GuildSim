import sys

# Ensure shared runtime modules are importable from /Core on Pico.
if "/Core" not in sys.path:
    sys.path.append("/Core")
if "Core" not in sys.path:
    sys.path.append("Core")

import guild_sim_kernel


def main():
    guild_sim_kernel.run()


if __name__ == "__main__":
    main()
