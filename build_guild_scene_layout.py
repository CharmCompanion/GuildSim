from __future__ import annotations

import json
from pathlib import Path


W, H = 128, 160

LAYOUT_PATH = Path("assets/layouts/dashboard.json")
SOURCE_IMAGES = [
    ("scenes/Guild/Guild1.1.png", 384, 480),
    ("scenes/Guild/Guild1.2.png", 192, 240),
    ("scenes/Guild/Guild1.4.png", 96, 120),
    ("scenes/Guild/Guild1.8.png", 48, 60),
]


def main() -> None:
    items: list[dict] = []
    for rel, sw, sh in SOURCE_IMAGES:
        # Center each source image on the 128x160 scene without scaling.
        x = (W - sw) // 2
        y = (H - sh) // 2
        items.append(
            {
                "type": "sprite",
                "layer_id": "base",
                "path": rel,
                "x": x,
                "y": y,
                "w": sw,
                "h": sh,
                "src_x": 0,
                "src_y": 0,
                "src_w": sw,
                "src_h": sh,
                "rot": 0,
                "flip_x": False,
                "flip_y": False,
            }
        )

    payload = {
        "scene": "dashboard",
        "bg": [10, 12, 16],
        "grid_cell": 8,
        "layer_defs": [{"id": "base", "name": "Base", "visible": True, "locked": False}],
        "active_layer_id": "base",
        "items": items,
    }

    LAYOUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    LAYOUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {LAYOUT_PATH} with {len(items)} centered sprites")


if __name__ == "__main__":
    main()
