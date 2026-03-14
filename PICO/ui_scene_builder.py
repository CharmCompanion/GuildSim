"""Scene layout builder for Pico 128x160 backgrounds.

Usage:
  python ui_scene_builder.py

Saves per-scene layout JSON files in assets/layouts/.
These are consumed by prepare_pico_assets.py when generating runtime backgrounds.
"""

from __future__ import annotations

import json
import math
import base64
import tkinter as tk
import time
from pathlib import Path
from tkinter import filedialog, ttk

from PIL import Image, ImageTk
from models import (
    ADVENTURE_BASES,
    ADVENTURE_ADDON_PARTS,
    build_adventure_seed_code,
    decode_adventure_seed_code,
)

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
LAYOUTS = ASSETS / "layouts"
RUNTIME_BG = ASSETS / "runtime" / "backgrounds"
CUSTOM_ADVENTURES_PATH = LAYOUTS / "custom_adventures.json"
SCENE_SEEDS_PATH = LAYOUTS / "scene_seeds.json"
SEED_LIBRARY_PATH = LAYOUTS / "seed_library.json"

SCENE_NAMES = {
    "save_slots": "save_slots.bmp",
    "dashboard": "guild_hall.bmp",
    "roster": "roster.bmp",
    "tavern": "tavern.bmp",
    "recruit": "recruit.bmp",
    "training": "training.bmp",
    "settings": "settings.bmp",
    "log": "log.bmp",
    "missions": "corrupted_tiles.bmp",
}

EDITABLE_SCENES = (
    "dashboard",
    "roster",
    "tavern",
    "recruit",
    "training",
    "missions",
)

W, H = 128, 160
DEFAULT_ZOOM = 4
MIN_ZOOM = 2
MAX_ZOOM = 12

DARK_BG = "#16181d"
DARK_PANEL = "#1f232b"
DARK_PANEL_ALT = "#252a34"
DARK_BORDER = "#323846"
TEXT_FG = "#e7ebf2"
MUTED_FG = "#aab3c2"
ACCENT = "#4a88ff"


class Builder:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("GuildSim Scene Builder")
        self._apply_dark_theme()
        self._set_initial_window_size()

        self.scene_var = tk.StringVar(value="dashboard")
        self.search_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Ready")
        self.tool_var = tk.StringVar(value="paint")

        self.cell_size_var = tk.IntVar(value=8)
        self.snap_var = tk.BooleanVar(value=True)
        self.show_grid_var = tk.BooleanVar(value=True)
        self.zoom_var = tk.IntVar(value=DEFAULT_ZOOM)
        self.view_mode_var = tk.StringVar(value="top")
        self.perspective_skew_var = tk.DoubleVar(value=0.35)
        self.perspective_scale_var = tk.DoubleVar(value=0.75)

        self.tilemap_mode_var = tk.BooleanVar(value=False)
        self.tile_eraser_var = tk.BooleanVar(value=False)
        self.brush_size_var = tk.IntVar(value=1)

        self.pivot_mode_var = tk.StringVar(value="center")
        self.pivot_x_var = tk.IntVar(value=W // 2)
        self.pivot_y_var = tk.IntVar(value=H // 2)

        self.text_value_var = tk.StringVar(value="New Text")
        self.text_color_var = tk.StringVar(value="#ffffff")
        self.shape_color_var = tk.StringVar(value="#ffffff")
        self.shape_width_var = tk.IntVar(value=1)

        self.char_base_var = tk.StringVar(value=ADVENTURE_BASES[0])
        self.char_hair_var = tk.StringVar(value=ADVENTURE_ADDON_PARTS["hair"][0])
        self.char_face_var = tk.StringVar(value=ADVENTURE_ADDON_PARTS["face"][0])
        self.char_outfit_var = tk.StringVar(value=ADVENTURE_ADDON_PARTS["outfit"][0])
        self.adv_name_var = tk.StringVar(value="Custom Adventure")
        self.adv_diff_var = tk.IntVar(value=2)
        self.adv_gold_var = tk.IntVar(value=120)
        self.adv_xp_var = tk.IntVar(value=45)
        self.adv_duration_var = tk.IntVar(value=40)
        self.adv_seed_var = tk.StringVar(value="")
        self.adv_preview_var = tk.StringVar(value="No seed yet")
        self.place_seed_var = tk.StringVar(value="")
        self.place_seed_info_var = tk.StringVar(value="No place seed yet")
        self.seed_filter_var = tk.StringVar(value="")
        self.seed_title_var = tk.StringVar(value="")
        self.seed_tags_var = tk.StringVar(value="")
        self.seed_author_var = tk.StringVar(value="")
        self.seed_description_var = tk.StringVar(value="")
        self.seed_rating_var = tk.StringVar(value="G")
        self.seed_created_var = tk.StringVar(value="")
        self.seed_updated_var = tk.StringVar(value="")
        self.seed_dep_status_var = tk.StringVar(value="Dependencies: n/a")
        self.remap_old_var = tk.StringVar(value="")
        self.remap_new_var = tk.StringVar(value="")
        self.import_strategy_var = tk.StringVar(value="replace")

        self.sprites: list[Path] = []
        self.item_rel_by_iid: dict[str, str] = {}
        self.iid_by_rel: dict[str, str] = {}
        self.items: list[dict] = []
        self.selected_indices: set[int] = set()
        self.selected_index: int | None = None

        self.drag_mode: str | None = None
        self.drag_start = (0, 0)
        self.drag_start_positions: dict[int, tuple[int, int]] = {}
        self.marquee_start: tuple[int, int] | None = None
        self.marquee_current: tuple[int, int] | None = None

        self.scale_handle: str | None = None
        self.scale_pivot: tuple[float, float] = (0.0, 0.0)
        self.scale_start_handle_pos: tuple[float, float] = (0.0, 0.0)
        self.scale_start_items: dict[int, dict] = {}
        self.rotate_start_items: dict[int, dict] = {}
        self.rotate_pivot: tuple[float, float] = (0.0, 0.0)
        self.rotate_start_angle: float = 0.0

        self.clipboard_items: list[dict] = []
        self.current_rel: str | None = None
        self.last_paint_key: tuple | None = None

        self.image_cache: dict[str, Image.Image] = {}
        self.tk_cache: dict[str, ImageTk.PhotoImage] = {}

        self.undo_stack: list[str] = []
        self.redo_stack: list[str] = []
        self.scene_seed_db: dict[str, str] = {}
        self.seed_library: list[dict] = []
        self.seed_dep_missing: list[str] = []
        self.layer_defs: list[dict] = [{"id": "base", "name": "Base", "visible": True, "locked": False}]
        self.active_layer_id = "base"
        self.layer_counter = 1
        self.mirror_guide_axis: str | None = None
        self._mirror_guide_job = None

        self.prop_vars = {
            "x": tk.IntVar(value=0),
            "y": tk.IntVar(value=0),
            "w": tk.IntVar(value=16),
            "h": tk.IntVar(value=16),
            "src_x": tk.IntVar(value=0),
            "src_y": tk.IntVar(value=0),
            "src_w": tk.IntVar(value=16),
            "src_h": tk.IntVar(value=16),
        }

        self.sheet_cols = 1
        self.sheet_rows = 1
        self.sheet_selected = (0, 0)
        self._last_resize_sig = (0, 0)

        self._build_ui()
        self._bind_shortcuts()
        self._scan_assets()
        self._refresh_tree()
        self._load_scene_seed_db()
        self._load_seed_library()
        self._render_canvas()
        self.root.bind("<Configure>", self._on_root_resize)

    def _set_initial_window_size(self) -> None:
        sw = max(800, int(self.root.winfo_screenwidth()))
        sh = max(600, int(self.root.winfo_screenheight()))
        w = min(1920, sw)
        h = min(1080, sh)
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.minsize(1100, 700)

    def _apply_dark_theme(self) -> None:
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        self.root.configure(bg=DARK_BG)
        self.root.option_add("*Listbox.Background", DARK_PANEL)
        self.root.option_add("*Listbox.Foreground", TEXT_FG)
        self.root.option_add("*Listbox.selectBackground", ACCENT)
        self.root.option_add("*Listbox.selectForeground", TEXT_FG)
        self.root.option_add("*Listbox.highlightBackground", DARK_BORDER)

        style.configure(".", background=DARK_BG, foreground=TEXT_FG)
        style.configure("TFrame", background=DARK_BG)
        style.configure("TLabelframe", background=DARK_BG, foreground=TEXT_FG, bordercolor=DARK_BORDER)
        style.configure("TLabelframe.Label", background=DARK_BG, foreground=TEXT_FG)
        style.configure("TLabel", background=DARK_BG, foreground=TEXT_FG)
        style.configure("TButton", background=DARK_PANEL_ALT, foreground=TEXT_FG, bordercolor=DARK_BORDER)
        style.map(
            "TButton",
            background=[("active", "#34405a"), ("pressed", "#2c3650")],
            foreground=[("disabled", MUTED_FG)],
        )
        style.configure("TCheckbutton", background=DARK_BG, foreground=TEXT_FG)
        style.configure("TRadiobutton", background=DARK_BG, foreground=TEXT_FG)
        style.configure("TSeparator", background=DARK_BORDER)

        style.configure(
            "TEntry",
            fieldbackground=DARK_PANEL,
            foreground=TEXT_FG,
            insertcolor=TEXT_FG,
            bordercolor=DARK_BORDER,
        )
        style.configure(
            "TSpinbox",
            fieldbackground=DARK_PANEL,
            foreground=TEXT_FG,
            insertcolor=TEXT_FG,
            bordercolor=DARK_BORDER,
            arrowsize=12,
        )
        style.configure(
            "TCombobox",
            fieldbackground=DARK_PANEL,
            foreground=TEXT_FG,
            background=DARK_PANEL_ALT,
            arrowcolor=TEXT_FG,
            bordercolor=DARK_BORDER,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", DARK_PANEL)],
            selectbackground=[("readonly", ACCENT)],
            selectforeground=[("readonly", TEXT_FG)],
            foreground=[("readonly", TEXT_FG)],
        )

        style.configure("Treeview", background=DARK_PANEL, fieldbackground=DARK_PANEL, foreground=TEXT_FG, bordercolor=DARK_BORDER)
        style.configure("Treeview.Heading", background=DARK_PANEL_ALT, foreground=TEXT_FG, bordercolor=DARK_BORDER)
        style.map("Treeview", background=[("selected", ACCENT)], foreground=[("selected", TEXT_FG)])

        style.configure("TNotebook", background=DARK_BG, bordercolor=DARK_BORDER)
        style.configure("TNotebook.Tab", background=DARK_PANEL_ALT, foreground=TEXT_FG, padding=(8, 4))
        style.map("TNotebook.Tab", background=[("selected", "#2f3747")], foreground=[("selected", TEXT_FG)])

        style.configure("TScrollbar", background=DARK_PANEL_ALT, troughcolor=DARK_PANEL, bordercolor=DARK_BORDER, arrowcolor=TEXT_FG)

    def _build_ui(self) -> None:
        top = ttk.Frame(self.root)
        top.pack(fill="x", padx=8, pady=6)

        ttk.Label(top, text="Scene").pack(side="left")
        scene_box = ttk.Combobox(top, width=14, textvariable=self.scene_var, values=list(EDITABLE_SCENES), state="readonly")
        scene_box.pack(side="left", padx=6)
        scene_box.bind("<<ComboboxSelected>>", lambda _e: self._load_scene())

        ttk.Button(top, text="Load", command=self._load_scene).pack(side="left", padx=2)
        ttk.Button(top, text="Save", command=self._save_scene).pack(side="left", padx=2)
        ttk.Button(top, text="Export BMP", command=self._export_bmp).pack(side="left", padx=2)
        ttk.Button(top, text="Clear", command=self._clear_scene).pack(side="left", padx=2)
        ttk.Button(top, text="Undo", command=self._undo).pack(side="left", padx=2)
        ttk.Button(top, text="Redo", command=self._redo).pack(side="left", padx=2)

        body = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        body.pack(fill="both", expand=True, padx=8, pady=4)
        self.body_pane = body

        left = ttk.Frame(body)
        center = ttk.Frame(body)
        right = ttk.Frame(body)
        self.left_panel = left
        self.center_panel = center
        self.right_panel = right
        body.add(left, weight=3)
        body.add(center, weight=5)
        body.add(right, weight=3)

        ttk.Label(left, text="Sprite Search").pack(anchor="w")
        search = ttk.Entry(left, textvariable=self.search_var)
        search.pack(fill="x", pady=(0, 4))
        search.bind("<KeyRelease>", lambda _e: self._refresh_tree())

        tree_frame = ttk.Frame(left)
        tree_frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(tree_frame, show="tree", selectmode="browse", height=18)
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", lambda _e: self._on_tree_select())
        self.tree.bind("<Double-1>", lambda _e: self._add_selected_sprite())

        left_btn = ttk.Frame(left)
        left_btn.pack(fill="x", pady=4)
        ttk.Button(left_btn, text="Add Sprite", command=self._add_selected_sprite).pack(side="left", padx=2)
        ttk.Button(left_btn, text="Browse", command=self._add_from_file).pack(side="left", padx=2)

        sheet_cfg = ttk.LabelFrame(left, text="Sheet Picker")
        sheet_cfg.pack(fill="x", pady=4)
        row = ttk.Frame(sheet_cfg)
        row.pack(fill="x")
        ttk.Label(row, text="Cell").pack(side="left")
        ttk.Entry(row, textvariable=self.cell_size_var, width=5).pack(side="left", padx=4)
        ttk.Checkbutton(row, text="Snap", variable=self.snap_var).pack(side="left", padx=4)

        self.preview_canvas = tk.Canvas(
            left,
            width=220,
            height=220,
            bg="#101010",
            highlightthickness=1,
            highlightbackground=DARK_BORDER,
        )
        self.preview_canvas.pack(fill="both", expand=True)
        self.preview_canvas.bind("<Button-1>", self._on_preview_click)
        self.preview_canvas.bind("<B1-Motion>", self._on_preview_drag)

        toolbar = ttk.Frame(center)
        toolbar.pack(fill="x", pady=(0, 4))

        ttk.Label(toolbar, text="Tools").pack(side="left")
        for tool in ["select", "paint", "line", "rect", "text", "char_marker", "enemy_marker"]:
            ttk.Radiobutton(toolbar, text=tool, value=tool, variable=self.tool_var).pack(side="left", padx=2)

        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=6)
        ttk.Button(toolbar, text="Copy", command=self._copy_selected).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Paste", command=self._paste_clipboard).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Duplicate", command=self._duplicate_selected).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Replace", command=self._replace_selected_sprite).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Delete", command=self._delete_selected_item).pack(side="left", padx=2)

        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=6)
        ttk.Button(toolbar, text="Rot L", command=lambda: self._rotate_selected(-90)).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Rot R", command=lambda: self._rotate_selected(90)).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Mirror L-R", command=lambda: self._flip_selected("h")).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Mirror T-B", command=lambda: self._flip_selected("v")).pack(side="left", padx=2)

        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=6)
        ttk.Label(toolbar, text="View").pack(side="left", padx=(0, 2))
        ttk.Combobox(toolbar, width=10, state="readonly", textvariable=self.view_mode_var, values=["top", "perspective"]).pack(side="left", padx=(0, 4))
        ttk.Checkbutton(toolbar, text="Grid", variable=self.show_grid_var, command=self._render_canvas).pack(side="left")
        ttk.Label(toolbar, text="Cell").pack(side="left", padx=(4, 1))
        ttk.Entry(toolbar, textvariable=self.cell_size_var, width=4).pack(side="left")
        ttk.Label(toolbar, text="Zoom").pack(side="left", padx=(4, 1))
        ttk.Entry(toolbar, textvariable=self.zoom_var, width=4).pack(side="left")
        ttk.Button(toolbar, text="Apply", command=self._apply_zoom_var).pack(side="left", padx=2)
        ttk.Label(toolbar, text="Skew").pack(side="left", padx=(4, 1))
        ttk.Entry(toolbar, textvariable=self.perspective_skew_var, width=4).pack(side="left")
        ttk.Label(toolbar, text="Y").pack(side="left", padx=(4, 1))
        ttk.Entry(toolbar, textvariable=self.perspective_scale_var, width=4).pack(side="left")
        ttk.Button(toolbar, text="View", command=self._apply_view_mode).pack(side="left", padx=2)
        ttk.Checkbutton(toolbar, text="Tilemap", variable=self.tilemap_mode_var).pack(side="left", padx=(4, 0))
        ttk.Checkbutton(toolbar, text="Eraser", variable=self.tile_eraser_var).pack(side="left", padx=(2, 0))
        ttk.Label(toolbar, text="Brush").pack(side="left", padx=(4, 1))
        ttk.Spinbox(toolbar, from_=1, to=8, textvariable=self.brush_size_var, width=3).pack(side="left")
        ttk.Label(toolbar, text="Pivot").pack(side="left", padx=(4, 1))
        ttk.Combobox(toolbar, width=8, state="readonly", textvariable=self.pivot_mode_var, values=["center", "topleft", "custom"]).pack(side="left")
        ttk.Label(toolbar, text="X").pack(side="left", padx=(4, 1))
        ttk.Entry(toolbar, textvariable=self.pivot_x_var, width=4).pack(side="left")
        ttk.Label(toolbar, text="Y").pack(side="left", padx=(4, 1))
        ttk.Entry(toolbar, textvariable=self.pivot_y_var, width=4).pack(side="left")

        self.canvas = tk.Canvas(
            center,
            width=W * DEFAULT_ZOOM,
            height=H * DEFAULT_ZOOM,
            bg="#111",
            highlightthickness=1,
            highlightbackground=DARK_BORDER,
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self.canvas.bind("<Button-4>", lambda _e: self._set_zoom(self.zoom_var.get() + 1))
        self.canvas.bind("<Button-5>", lambda _e: self._set_zoom(self.zoom_var.get() - 1))

        ttk.Label(
            center,
            text="Shift+drag: marquee add. Drag cyan handles: scale selection. Right-click in tilemap mode: flood fill. View can be top or perspective.",
            anchor="w",
        ).pack(fill="x", pady=(4, 0))

        right_tabs = ttk.Notebook(right)
        right_tabs.pack(fill="both", expand=True)
        self.mode_tabs = right_tabs

        tab_edit = ttk.Frame(right_tabs)
        tab_adv = ttk.Frame(right_tabs)
        tab_seed = ttk.Frame(right_tabs)
        right_tabs.add(tab_edit, text="Layer/Edit")
        right_tabs.add(tab_adv, text="Adventure")
        right_tabs.add(tab_seed, text="Seeds/Library")
        right_tabs.bind("<<NotebookTabChanged>>", self._on_mode_tab_changed)

        layer_box = ttk.LabelFrame(tab_edit, text="Scene Layers")
        layer_box.pack(fill="x", pady=4)
        self.layer_defs_list = tk.Listbox(
            layer_box,
            height=5,
            selectmode=tk.EXTENDED,
            bg=DARK_PANEL,
            fg=TEXT_FG,
            selectbackground=ACCENT,
            selectforeground=TEXT_FG,
            highlightbackground=DARK_BORDER,
        )
        self.layer_defs_list.pack(fill="x", padx=2, pady=2)
        self.layer_defs_list.bind("<<ListboxSelect>>", lambda _e: self._on_layer_def_select())

        layer_btns = ttk.Frame(layer_box)
        layer_btns.pack(fill="x", padx=2, pady=(0, 2))
        ttk.Button(layer_btns, text="New", command=self._new_layer).pack(side="left", padx=1)
        ttk.Button(layer_btns, text="Duplicate", command=self._duplicate_layers).pack(side="left", padx=1)
        ttk.Button(layer_btns, text="Remove", command=self._remove_layers).pack(side="left", padx=1)
        ttk.Button(layer_btns, text="Hide/Show", command=self._toggle_layers_visibility).pack(side="left", padx=1)
        ttk.Button(layer_btns, text="Lock/Unlock", command=self._toggle_layers_lock).pack(side="left", padx=1)
        ttk.Button(layer_btns, text="Assign Selected", command=self._assign_selected_to_active_layer).pack(side="left", padx=1)

        ttk.Label(tab_edit, text="Layers (top is drawn last)").pack(anchor="w")
        self.layers_list = tk.Listbox(
            tab_edit,
            height=12,
            selectmode=tk.EXTENDED,
            bg=DARK_PANEL,
            fg=TEXT_FG,
            selectbackground=ACCENT,
            selectforeground=TEXT_FG,
            highlightbackground=DARK_BORDER,
        )
        self.layers_list.pack(fill="x")
        self.layers_list.bind("<<ListboxSelect>>", lambda _e: self._on_layer_select())

        lr = ttk.Frame(tab_edit)
        lr.pack(fill="x", pady=4)
        ttk.Button(lr, text="Up", command=self._layer_up).pack(side="left", padx=2)
        ttk.Button(lr, text="Down", command=self._layer_down).pack(side="left", padx=2)
        ttk.Button(lr, text="Top", command=self._layer_top).pack(side="left", padx=2)
        ttk.Button(lr, text="Bottom", command=self._layer_bottom).pack(side="left", padx=2)

        prop = ttk.LabelFrame(tab_edit, text="Selected Properties")
        prop.pack(fill="x", pady=4)
        for key in ("x", "y", "w", "h", "src_x", "src_y", "src_w", "src_h"):
            rowp = ttk.Frame(prop)
            rowp.pack(fill="x", pady=1)
            ttk.Label(rowp, text=key.upper(), width=6).pack(side="left")
            ttk.Entry(rowp, textvariable=self.prop_vars[key], width=8).pack(side="left")
        ttk.Button(prop, text="Apply", command=self._apply_props).pack(fill="x", pady=3)

        style_box = ttk.LabelFrame(tab_edit, text="Text / Shape")
        style_box.pack(fill="x", pady=4)
        ttk.Entry(style_box, textvariable=self.text_value_var).pack(fill="x", pady=2)
        sr1 = ttk.Frame(style_box)
        sr1.pack(fill="x", pady=2)
        ttk.Label(sr1, text="Text Color").pack(side="left")
        ttk.Entry(sr1, textvariable=self.text_color_var, width=10).pack(side="left", padx=4)
        sr2 = ttk.Frame(style_box)
        sr2.pack(fill="x", pady=2)
        ttk.Label(sr2, text="Shape Color").pack(side="left")
        ttk.Entry(sr2, textvariable=self.shape_color_var, width=10).pack(side="left", padx=4)
        ttk.Label(sr2, text="Stroke").pack(side="left")
        ttk.Entry(sr2, textvariable=self.shape_width_var, width=4).pack(side="left", padx=4)

        # Adventure tab: character base + addons, custom mission stats, and shareable seed.
        char_box = ttk.LabelFrame(tab_adv, text="Character Builder")
        char_box.pack(fill="x", pady=4)
        ttk.Label(char_box, text="Base").pack(anchor="w")
        ttk.Combobox(char_box, textvariable=self.char_base_var, values=ADVENTURE_BASES, state="readonly").pack(fill="x", pady=1)
        ttk.Label(char_box, text="Hair Addon").pack(anchor="w")
        ttk.Combobox(char_box, textvariable=self.char_hair_var, values=ADVENTURE_ADDON_PARTS["hair"], state="readonly").pack(fill="x", pady=1)
        ttk.Label(char_box, text="Face Addon").pack(anchor="w")
        ttk.Combobox(char_box, textvariable=self.char_face_var, values=ADVENTURE_ADDON_PARTS["face"], state="readonly").pack(fill="x", pady=1)
        ttk.Label(char_box, text="Outfit Addon").pack(anchor="w")
        ttk.Combobox(char_box, textvariable=self.char_outfit_var, values=ADVENTURE_ADDON_PARTS["outfit"], state="readonly").pack(fill="x", pady=1)

        adv_box = ttk.LabelFrame(tab_adv, text="Adventure Stats")
        adv_box.pack(fill="x", pady=4)
        ttk.Label(adv_box, text="Name").pack(anchor="w")
        ttk.Entry(adv_box, textvariable=self.adv_name_var).pack(fill="x", pady=1)
        adv_row1 = ttk.Frame(adv_box)
        adv_row1.pack(fill="x", pady=1)
        ttk.Label(adv_row1, text="Diff").pack(side="left")
        ttk.Spinbox(adv_row1, from_=1, to=9, textvariable=self.adv_diff_var, width=5).pack(side="left", padx=2)
        ttk.Label(adv_row1, text="Gold").pack(side="left", padx=(8, 0))
        ttk.Entry(adv_row1, textvariable=self.adv_gold_var, width=7).pack(side="left", padx=2)
        ttk.Label(adv_row1, text="XP").pack(side="left", padx=(8, 0))
        ttk.Entry(adv_row1, textvariable=self.adv_xp_var, width=7).pack(side="left", padx=2)
        adv_row2 = ttk.Frame(adv_box)
        adv_row2.pack(fill="x", pady=1)
        ttk.Label(adv_row2, text="Duration").pack(side="left")
        ttk.Entry(adv_row2, textvariable=self.adv_duration_var, width=7).pack(side="left", padx=2)

        seed_box = ttk.LabelFrame(tab_adv, text="Seed Code")
        seed_box.pack(fill="x", pady=4)
        ttk.Entry(seed_box, textvariable=self.adv_seed_var).pack(fill="x", pady=1)
        seed_btns = ttk.Frame(seed_box)
        seed_btns.pack(fill="x", pady=2)
        ttk.Button(seed_btns, text="Generate", command=self._generate_adventure_seed).pack(side="left", padx=2)
        ttk.Button(seed_btns, text="Load", command=self._load_adventure_seed).pack(side="left", padx=2)
        ttk.Button(seed_btns, text="Save Custom", command=self._save_custom_adventure).pack(side="left", padx=2)
        self.adv_preview_label = ttk.Label(seed_box, textvariable=self.adv_preview_var, wraplength=220, justify="left")
        self.adv_preview_label.pack(fill="x", pady=2)

        place_box = ttk.LabelFrame(tab_seed, text="Place / Scene Seed")
        place_box.pack(fill="x", pady=4)
        ttk.Label(place_box, text="Current Scene Seed").pack(anchor="w")
        ttk.Entry(place_box, textvariable=self.place_seed_var).pack(fill="x", pady=1)
        place_btns = ttk.Frame(place_box)
        place_btns.pack(fill="x", pady=2)
        ttk.Button(place_btns, text="Generate", command=self._generate_scene_seed_current).pack(side="left", padx=2)
        ttk.Button(place_btns, text="Load", command=self._load_scene_seed_from_entry).pack(side="left", padx=2)
        ttk.Button(place_btns, text="Copy", command=self._copy_place_seed).pack(side="left", padx=2)
        self.place_seed_info_label = ttk.Label(place_box, textvariable=self.place_seed_info_var, wraplength=220, justify="left")
        self.place_seed_info_label.pack(fill="x", pady=2)

        pack_box = ttk.LabelFrame(tab_seed, text="Seed Pack")
        pack_box.pack(fill="x", pady=4)
        ttk.Button(pack_box, text="Generate All Scene Seeds", command=self._generate_all_scene_seeds).pack(fill="x", padx=2, pady=1)
        ttk.Button(pack_box, text="Export Seed Pack", command=self._export_seed_pack).pack(fill="x", padx=2, pady=1)
        ttk.Button(pack_box, text="Import Seed Pack", command=self._import_seed_pack).pack(fill="x", padx=2, pady=1)

        lib_search = ttk.LabelFrame(tab_seed, text="Find")
        lib_search.pack(fill="x", pady=4)
        ttk.Entry(lib_search, textvariable=self.seed_filter_var).pack(fill="x", padx=2, pady=2)
        ttk.Button(lib_search, text="Refresh", command=self._refresh_seed_library_list).pack(fill="x", padx=2, pady=1)

        lib_list_frame = ttk.Frame(tab_seed)
        lib_list_frame.pack(fill="both", expand=True)
        self.seed_library_list = tk.Listbox(
            lib_list_frame,
            height=12,
            bg=DARK_PANEL,
            fg=TEXT_FG,
            selectbackground=ACCENT,
            selectforeground=TEXT_FG,
            highlightbackground=DARK_BORDER,
        )
        lib_scroll = ttk.Scrollbar(lib_list_frame, orient="vertical", command=self.seed_library_list.yview)
        self.seed_library_list.configure(yscrollcommand=lib_scroll.set)
        self.seed_library_list.pack(side="left", fill="both", expand=True)
        lib_scroll.pack(side="right", fill="y")
        self.seed_library_list.bind("<<ListboxSelect>>", lambda _e: self._on_seed_library_select())

        lib_meta = ttk.LabelFrame(tab_seed, text="Metadata")
        lib_meta.pack(fill="x", pady=4)
        ttk.Label(lib_meta, text="Title").pack(anchor="w")
        ttk.Entry(lib_meta, textvariable=self.seed_title_var).pack(fill="x", padx=2, pady=1)
        ttk.Label(lib_meta, text="Author").pack(anchor="w")
        ttk.Entry(lib_meta, textvariable=self.seed_author_var).pack(fill="x", padx=2, pady=1)
        ttk.Label(lib_meta, text="Description").pack(anchor="w")
        ttk.Entry(lib_meta, textvariable=self.seed_description_var).pack(fill="x", padx=2, pady=1)
        ttk.Label(lib_meta, text="Rating").pack(anchor="w")
        ttk.Combobox(lib_meta, textvariable=self.seed_rating_var, values=["G", "PG", "T", "M"], state="readonly").pack(fill="x", padx=2, pady=1)
        ttk.Label(lib_meta, text="Tags (comma)").pack(anchor="w")
        ttk.Entry(lib_meta, textvariable=self.seed_tags_var).pack(fill="x", padx=2, pady=1)
        ttk.Label(lib_meta, text="Created").pack(anchor="w")
        ttk.Entry(lib_meta, textvariable=self.seed_created_var, state="readonly").pack(fill="x", padx=2, pady=1)
        ttk.Label(lib_meta, text="Updated").pack(anchor="w")
        ttk.Entry(lib_meta, textvariable=self.seed_updated_var, state="readonly").pack(fill="x", padx=2, pady=1)

        dep_box = ttk.LabelFrame(tab_seed, text="Dependency Check / Remap")
        dep_box.pack(fill="x", pady=4)
        self.seed_dep_status_label = ttk.Label(dep_box, textvariable=self.seed_dep_status_var, wraplength=220, justify="left")
        self.seed_dep_status_label.pack(fill="x", padx=2, pady=1)
        ttk.Button(dep_box, text="Check Selected Dependencies", command=self._check_selected_dependencies).pack(fill="x", padx=2, pady=1)
        ttk.Label(dep_box, text="Missing Path").pack(anchor="w")
        ttk.Entry(dep_box, textvariable=self.remap_old_var).pack(fill="x", padx=2, pady=1)
        ttk.Label(dep_box, text="Remap To Path").pack(anchor="w")
        ttk.Entry(dep_box, textvariable=self.remap_new_var).pack(fill="x", padx=2, pady=1)
        ttk.Button(dep_box, text="Apply Remap To Selected", command=self._remap_selected_seed_path).pack(fill="x", padx=2, pady=1)

        import_box = ttk.LabelFrame(tab_seed, text="Import Mode")
        import_box.pack(fill="x", pady=4)
        ttk.Combobox(import_box, textvariable=self.import_strategy_var, values=["replace", "skip", "duplicate"], state="readonly").pack(fill="x", padx=2, pady=1)

        lib_btns = ttk.LabelFrame(tab_seed, text="Actions")
        lib_btns.pack(fill="x", pady=4)
        ttk.Button(lib_btns, text="Add Current Place", command=self._add_current_place_to_library).pack(fill="x", padx=2, pady=1)
        ttk.Button(lib_btns, text="Add Current Adventure", command=self._add_current_adventure_to_library).pack(fill="x", padx=2, pady=1)
        ttk.Button(lib_btns, text="Save Metadata", command=self._save_selected_library_metadata).pack(fill="x", padx=2, pady=1)
        ttk.Button(lib_btns, text="Load Selected", command=self._load_selected_library_seed).pack(fill="x", padx=2, pady=1)
        ttk.Button(lib_btns, text="Delete Selected", command=self._delete_selected_library_seed).pack(fill="x", padx=2, pady=1)
        ttk.Button(lib_btns, text="Export Library", command=self._export_seed_library).pack(fill="x", padx=2, pady=1)
        ttk.Button(lib_btns, text="Import Library", command=self._import_seed_library).pack(fill="x", padx=2, pady=1)

        ttk.Label(self.root, textvariable=self.status_var, anchor="w").pack(fill="x", padx=8, pady=(0, 6))
        self._on_mode_tab_changed(None)

    def _on_mode_tab_changed(self, _event) -> None:
        if not hasattr(self, "mode_tabs"):
            return
        cur = str(self.mode_tabs.tab(self.mode_tabs.select(), "text")).strip().lower()
        scene_mode = cur.startswith("layer")

        for pane in list(self.body_pane.panes()):
            self.body_pane.forget(pane)

        if scene_mode:
            self.body_pane.add(self.left_panel, weight=3)
            self.body_pane.add(self.center_panel, weight=5)
            self.body_pane.add(self.right_panel, weight=3)
            self.status_var.set("Scene editing mode")
        else:
            self.body_pane.add(self.right_panel, weight=1)
            if cur.startswith("adventure"):
                self.status_var.set("Adventure creator mode")
            else:
                self.status_var.set("Seeds and library mode")

    def _on_root_resize(self, _event) -> None:
        sig = (int(self.root.winfo_width()), int(self.root.winfo_height()))
        if sig == self._last_resize_sig:
            return
        self._last_resize_sig = sig

        wrap = max(180, min(560, int(self.right_panel.winfo_width()) - 28)) if hasattr(self, "right_panel") else 220
        if hasattr(self, "adv_preview_label"):
            self.adv_preview_label.configure(wraplength=wrap)
        if hasattr(self, "place_seed_info_label"):
            self.place_seed_info_label.configure(wraplength=wrap)
        if hasattr(self, "seed_dep_status_label"):
            self.seed_dep_status_label.configure(wraplength=wrap)

        if self.current_rel:
            self._update_sprite_preview(self.current_rel)

    def _preview_metrics(self, iw: int, ih: int) -> tuple[int, int, int, int, int, int]:
        cw = max(80, int(self.preview_canvas.winfo_width()))
        ch = max(80, int(self.preview_canvas.winfo_height()))
        box_w = max(40, cw - 10)
        box_h = max(40, ch - 10)
        scale = min(box_w / float(iw), box_h / float(ih))
        nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
        ox = (cw - nw) // 2
        oy = (ch - nh) // 2
        return cw, ch, nw, nh, ox, oy

    def _bind_shortcuts(self) -> None:
        self.root.bind("<Delete>", lambda _e: self._delete_selected_item())
        self.root.bind("<Control-z>", lambda _e: self._undo())
        self.root.bind("<Control-y>", lambda _e: self._redo())
        self.root.bind("<Control-d>", lambda _e: self._duplicate_selected())
        self.root.bind("<Control-c>", lambda _e: self._copy_selected())
        self.root.bind("<Control-v>", lambda _e: self._paste_clipboard())

        self.root.bind("<Up>", lambda _e: self._nudge(0, -1))
        self.root.bind("<Down>", lambda _e: self._nudge(0, 1))
        self.root.bind("<Left>", lambda _e: self._nudge(-1, 0))
        self.root.bind("<Right>", lambda _e: self._nudge(1, 0))

        self.root.bind("<Control-plus>", lambda _e: self._set_zoom(self.zoom_var.get() + 1))
        self.root.bind("<Control-equal>", lambda _e: self._set_zoom(self.zoom_var.get() + 1))
        self.root.bind("<Control-minus>", lambda _e: self._set_zoom(self.zoom_var.get() - 1))
        self.root.bind("<Control-0>", lambda _e: self._set_zoom(DEFAULT_ZOOM))

    def _character_indices(self) -> dict:
        def idx_of(lst, value):
            try:
                return lst.index(value)
            except ValueError:
                return 0

        return {
            "base_idx": idx_of(ADVENTURE_BASES, self.char_base_var.get()),
            "hair_idx": idx_of(ADVENTURE_ADDON_PARTS["hair"], self.char_hair_var.get()),
            "face_idx": idx_of(ADVENTURE_ADDON_PARTS["face"], self.char_face_var.get()),
            "outfit_idx": idx_of(ADVENTURE_ADDON_PARTS["outfit"], self.char_outfit_var.get()),
        }

    def _generate_adventure_seed(self) -> None:
        parts = self._character_indices()
        variant = int(time.time()) % 10000
        code = build_adventure_seed_code(
            {
                "difficulty": int(self.adv_diff_var.get()),
                "gold_reward": int(self.adv_gold_var.get()),
                "xp_reward": int(self.adv_xp_var.get()),
                "duration": int(self.adv_duration_var.get()),
                "variant": variant,
            },
            parts,
        )
        self.adv_seed_var.set(code)
        self._load_adventure_seed()

    def _load_adventure_seed(self) -> None:
        code = self.adv_seed_var.get().strip()
        payload = decode_adventure_seed_code(code)
        if not payload:
            self.adv_preview_var.set("Invalid seed code")
            return

        self.adv_diff_var.set(int(payload.get("difficulty", 1)))
        self.adv_gold_var.set(int(payload.get("gold_reward", 0)))
        self.adv_xp_var.set(int(payload.get("xp_reward", 0)))
        self.adv_duration_var.set(int(payload.get("duration", 30)))
        self.adv_name_var.set(payload.get("name", "Custom Adventure"))

        c = payload.get("character_seed", {})
        if c:
            self.char_base_var.set(c.get("base", self.char_base_var.get()))
            self.char_hair_var.set(c.get("hair", self.char_hair_var.get()))
            self.char_face_var.set(c.get("face", self.char_face_var.get()))
            self.char_outfit_var.set(c.get("outfit", self.char_outfit_var.get()))

        line1 = payload.get("name", "Adventure") + " | D" + str(payload.get("difficulty", 1))
        line2 = "Gold " + str(payload.get("gold_reward", 0)) + " XP " + str(payload.get("xp_reward", 0))
        line3 = "Build: " + c.get("base", "?") + " + " + c.get("hair", "?") + "/" + c.get("face", "?") + "/" + c.get("outfit", "?")
        self.adv_preview_var.set(line1 + "\n" + line2 + "\n" + line3)

    def _save_custom_adventure(self) -> None:
        code = self.adv_seed_var.get().strip()
        payload = decode_adventure_seed_code(code)
        if not payload:
            self.status_var.set("Invalid seed code")
            return

        CUSTOM_ADVENTURES_PATH.parent.mkdir(parents=True, exist_ok=True)
        existing = []
        if CUSTOM_ADVENTURES_PATH.exists():
            try:
                existing = json.loads(CUSTOM_ADVENTURES_PATH.read_text(encoding="utf-8"))
            except Exception:
                existing = []

        if not isinstance(existing, list):
            existing = []

        entry = {
            "name": self.adv_name_var.get().strip() or payload.get("name", "Custom Adventure"),
            "seed_code": payload.get("seed_code", code),
            "difficulty": int(payload.get("difficulty", 1)),
            "gold_reward": int(payload.get("gold_reward", 0)),
            "xp_reward": int(payload.get("xp_reward", 0)),
            "duration": int(payload.get("duration", 30)),
            "character_seed": payload.get("character_seed", {}),
        }

        found = False
        for i, e in enumerate(existing):
            if e.get("seed_code") == entry["seed_code"]:
                existing[i] = entry
                found = True
                break
        if not found:
            existing.append(entry)

        CUSTOM_ADVENTURES_PATH.write_text(json.dumps(existing, indent=2), encoding="utf-8")
        self._upsert_library_entry(
            {
                "seed_code": entry["seed_code"],
                "kind": "adventure",
                "title": entry["name"],
                "tags": ["adventure", "custom"],
                "meta": {
                    "difficulty": entry["difficulty"],
                    "gold_reward": entry["gold_reward"],
                    "xp_reward": entry["xp_reward"],
                    "duration": entry["duration"],
                },
            }
        )
        self.status_var.set("Saved custom adventure seed")

    def _load_seed_library(self) -> None:
        self.seed_library = []
        if SEED_LIBRARY_PATH.exists():
            try:
                data = json.loads(SEED_LIBRARY_PATH.read_text(encoding="utf-8"))
            except Exception:
                data = []
            if isinstance(data, list):
                for e in data:
                    if not isinstance(e, dict):
                        continue
                    code = str(e.get("seed_code", "")).strip()
                    if not code:
                        continue
                    self.seed_library.append(e)
        self._refresh_seed_library_list()

    def _save_seed_library(self) -> None:
        SEED_LIBRARY_PATH.parent.mkdir(parents=True, exist_ok=True)
        SEED_LIBRARY_PATH.write_text(json.dumps(self.seed_library, indent=2), encoding="utf-8")

    def _now_iso(self) -> str:
        return time.strftime("%Y-%m-%d %H:%M:%S")

    def _upsert_library_entry(self, entry: dict) -> None:
        code = str(entry.get("seed_code", "")).strip()
        if not code:
            return
        entry_id = str(entry.get("entry_id", "")).strip() or code
        entry["entry_id"] = entry_id
        created = self._now_iso()
        updated = created
        hit = False
        for i, e in enumerate(self.seed_library):
            if str(e.get("entry_id", e.get("seed_code", "")).strip()) == entry_id:
                created = str(e.get("created_at", created))
                self.seed_library[i] = entry
                hit = True
                break
        if not hit:
            self.seed_library.append(entry)
        entry["created_at"] = created
        entry["updated_at"] = updated
        if "author" not in entry:
            entry["author"] = self.seed_author_var.get().strip()
        if "description" not in entry:
            entry["description"] = self.seed_description_var.get().strip()
        if "rating" not in entry:
            entry["rating"] = self.seed_rating_var.get().strip() or "G"
        self._save_seed_library()
        self._refresh_seed_library_list()

    def _filtered_seed_library(self) -> list[dict]:
        q = self.seed_filter_var.get().strip().lower()
        if not q:
            return list(self.seed_library)
        out = []
        for e in self.seed_library:
            title = str(e.get("title", "")).lower()
            code = str(e.get("seed_code", "")).lower()
            kind = str(e.get("kind", "")).lower()
            tags = ",".join([str(t).lower() for t in e.get("tags", [])])
            hay = " ".join([title, code, kind, tags])
            if q in hay:
                out.append(e)
        return out

    def _refresh_seed_library_list(self) -> None:
        if not hasattr(self, "seed_library_list"):
            return
        self.seed_library_list.delete(0, tk.END)
        for e in self._filtered_seed_library():
            kind = str(e.get("kind", "seed"))
            title = str(e.get("title", "Untitled"))
            rating = str(e.get("rating", "G"))
            code = str(e.get("seed_code", ""))
            self.seed_library_list.insert(tk.END, (kind + " | " + rating + " | " + title + " | " + code)[:95])

    def _selected_library_entry(self) -> dict | None:
        if not hasattr(self, "seed_library_list"):
            return None
        sel = self.seed_library_list.curselection()
        if not sel:
            return None
        idx = int(sel[0])
        items = self._filtered_seed_library()
        if idx < 0 or idx >= len(items):
            return None
        return items[idx]

    def _on_seed_library_select(self) -> None:
        e = self._selected_library_entry()
        if not e:
            return
        self.seed_title_var.set(str(e.get("title", "")))
        self.seed_author_var.set(str(e.get("author", "")))
        self.seed_description_var.set(str(e.get("description", "")))
        self.seed_rating_var.set(str(e.get("rating", "G")))
        self.seed_created_var.set(str(e.get("created_at", "")))
        self.seed_updated_var.set(str(e.get("updated_at", "")))
        tags = e.get("tags", [])
        if isinstance(tags, list):
            self.seed_tags_var.set(", ".join([str(t) for t in tags]))
        self._check_selected_dependencies()

    def _save_selected_library_metadata(self) -> None:
        e = self._selected_library_entry()
        if not e:
            self.status_var.set("No seed selected")
            return
        entry_id = str(e.get("entry_id", e.get("seed_code", ""))).strip()
        for item in self.seed_library:
            if str(item.get("entry_id", item.get("seed_code", ""))).strip() != entry_id:
                continue
            item["title"] = self.seed_title_var.get().strip() or item.get("title", "Untitled")
            item["author"] = self.seed_author_var.get().strip()
            item["description"] = self.seed_description_var.get().strip()
            item["rating"] = self.seed_rating_var.get().strip() or "G"
            item["tags"] = [t.strip() for t in self.seed_tags_var.get().split(",") if t.strip()]
            item["updated_at"] = self._now_iso()
            self.seed_updated_var.set(item["updated_at"])
            break
        self._save_seed_library()
        self._refresh_seed_library_list()
        self.status_var.set("Saved metadata")

    def _extract_place_dependencies(self, seed_code: str) -> list[str]:
        payload = self._decode_seed("PLC", seed_code)
        if not payload:
            return []
        deps: list[str] = []
        for it in payload.get("items", []):
            if isinstance(it, dict) and it.get("type") == "sprite":
                p = str(it.get("path", "")).strip()
                if p and p not in deps:
                    deps.append(p)
        return deps

    def _check_selected_dependencies(self) -> None:
        e = self._selected_library_entry()
        if not e:
            self.seed_dep_status_var.set("Dependencies: n/a")
            self.seed_dep_missing = []
            return
        code = str(e.get("seed_code", ""))
        if not code.startswith("PLC-"):
            self.seed_dep_status_var.set("Dependencies: not a place seed")
            self.seed_dep_missing = []
            return
        deps = self._extract_place_dependencies(code)
        missing = []
        for rel in deps:
            if not (ASSETS / rel).exists():
                missing.append(rel)
        self.seed_dep_missing = missing
        if missing:
            self.seed_dep_status_var.set("Missing " + str(len(missing)) + " asset(s)")
            self.remap_old_var.set(missing[0])
        else:
            self.seed_dep_status_var.set("Dependencies OK: " + str(len(deps)) + " assets")
            self.remap_old_var.set("")

    def _remap_selected_seed_path(self) -> None:
        e = self._selected_library_entry()
        if not e:
            self.status_var.set("No seed selected")
            return
        code = str(e.get("seed_code", "")).strip()
        if not code.startswith("PLC-"):
            self.status_var.set("Selected seed is not place type")
            return
        old_path = self.remap_old_var.get().strip()
        new_path = self.remap_new_var.get().strip().replace("\\", "/")
        if not old_path or not new_path:
            self.status_var.set("Set old and new paths")
            return
        if not (ASSETS / new_path).exists():
            self.status_var.set("New path not found in assets")
            return
        payload = self._decode_seed("PLC", code)
        if not payload:
            self.status_var.set("Invalid place seed")
            return
        changed = 0
        for it in payload.get("items", []):
            if isinstance(it, dict) and it.get("type") == "sprite" and str(it.get("path", "")).strip() == old_path:
                it["path"] = new_path
                changed += 1
        if changed <= 0:
            self.status_var.set("No matching paths in seed")
            return
        new_code = self._build_scene_seed(payload)
        self._upsert_library_entry(
            {
                "seed_code": new_code,
                "kind": "place",
                "title": self.seed_title_var.get().strip() or str(e.get("title", "Place")),
                "author": self.seed_author_var.get().strip() or str(e.get("author", "")),
                "description": self.seed_description_var.get().strip() or str(e.get("description", "")),
                "rating": self.seed_rating_var.get().strip() or str(e.get("rating", "G")),
                "tags": [t.strip() for t in self.seed_tags_var.get().split(",") if t.strip()],
                "meta": {
                    "scene": payload.get("scene", self.scene_var.get()),
                    "dependencies": self._extract_place_dependencies(new_code),
                },
            }
        )
        self.place_seed_var.set(new_code)
        self._check_selected_dependencies()
        self.status_var.set("Remapped " + str(changed) + " item(s)")

    def _add_current_place_to_library(self) -> None:
        seed = self.place_seed_var.get().strip()
        if not seed:
            self._generate_scene_seed_current()
            seed = self.place_seed_var.get().strip()
        payload = self._decode_seed("PLC", seed)
        if not payload:
            self.status_var.set("Invalid place seed")
            return
        title = self.seed_title_var.get().strip() or ("Place " + payload.get("scene", self.scene_var.get()))
        tags = [t.strip() for t in self.seed_tags_var.get().split(",") if t.strip()]
        self._upsert_library_entry(
            {
                "seed_code": seed,
                "kind": "place",
                "title": title,
                "tags": tags,
                "author": self.seed_author_var.get().strip(),
                "description": self.seed_description_var.get().strip(),
                "rating": self.seed_rating_var.get().strip() or "G",
                "meta": {
                    "scene": payload.get("scene", self.scene_var.get()),
                    "dependencies": self._extract_place_dependencies(seed),
                },
            }
        )
        self.status_var.set("Added place seed to library")

    def _add_current_adventure_to_library(self) -> None:
        seed = self.adv_seed_var.get().strip()
        payload = decode_adventure_seed_code(seed)
        if not payload:
            self.status_var.set("Invalid adventure seed")
            return
        title = self.seed_title_var.get().strip() or payload.get("name", "Adventure")
        tags = [t.strip() for t in self.seed_tags_var.get().split(",") if t.strip()]
        self._upsert_library_entry(
            {
                "seed_code": seed,
                "kind": "adventure",
                "title": title,
                "tags": tags,
                "author": self.seed_author_var.get().strip(),
                "description": self.seed_description_var.get().strip(),
                "rating": self.seed_rating_var.get().strip() or "G",
                "meta": {
                    "difficulty": payload.get("difficulty", 1),
                    "gold_reward": payload.get("gold_reward", 0),
                    "xp_reward": payload.get("xp_reward", 0),
                    "duration": payload.get("duration", 30),
                },
            }
        )
        self.status_var.set("Added adventure seed to library")

    def _load_selected_library_seed(self) -> None:
        e = self._selected_library_entry()
        if not e:
            self.status_var.set("No seed selected")
            return
        code = str(e.get("seed_code", "")).strip()
        kind = str(e.get("kind", "")).strip().lower()
        if kind == "place" or code.startswith("PLC-"):
            self.place_seed_var.set(code)
            self._load_scene_seed_from_entry()
            return
        if kind == "adventure" or code.startswith("ADV-"):
            self.adv_seed_var.set(code)
            self._load_adventure_seed()
            self.status_var.set("Loaded adventure seed from library")
            return
        self.status_var.set("Unknown seed type")

    def _delete_selected_library_seed(self) -> None:
        e = self._selected_library_entry()
        if not e:
            self.status_var.set("No seed selected")
            return
        code = str(e.get("seed_code", "")).strip()
        entry_id = str(e.get("entry_id", code)).strip()
        self.seed_library = [x for x in self.seed_library if str(x.get("entry_id", x.get("seed_code", "")).strip()) != entry_id]
        self._save_seed_library()
        self._refresh_seed_library_list()
        self.status_var.set("Deleted seed from library")

    def _export_seed_library(self) -> None:
        fp = filedialog.asksaveasfilename(
            title="Export Seed Library",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialdir=str(LAYOUTS),
            initialfile="seed_library_export.json",
        )
        if not fp:
            return
        payload = {"type": "guildsim_seed_library", "version": 1, "items": self.seed_library}
        Path(fp).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self.status_var.set("Exported seed library")

    def _import_seed_library(self) -> None:
        fp = filedialog.askopenfilename(
            title="Import Seed Library",
            filetypes=[("JSON files", "*.json")],
            initialdir=str(LAYOUTS),
        )
        if not fp:
            return
        try:
            payload = json.loads(Path(fp).read_text(encoding="utf-8"))
        except Exception:
            self.status_var.set("Invalid library file")
            return
        if Path(fp).stat().st_size > 2_000_000:
            self.status_var.set("Library file too large")
            return
        items = payload.get("items", []) if isinstance(payload, dict) else []
        if not isinstance(items, list):
            self.status_var.set("Invalid library file")
            return
        if len(items) > 1000:
            items = items[:1000]
        added = 0
        strategy = self.import_strategy_var.get().strip().lower()
        for e in items:
            if not isinstance(e, dict):
                continue
            code = str(e.get("seed_code", "")).strip()
            if not code:
                continue
            if code.startswith("PLC-") and not self._decode_seed("PLC", code):
                continue
            if code.startswith("ADV-") and not decode_adventure_seed_code(code):
                continue
            exists = any(str(x.get("seed_code", "")).strip() == code for x in self.seed_library)
            if exists and strategy == "skip":
                continue
            if exists and strategy == "duplicate":
                e = dict(e)
                e["entry_id"] = code + ":" + str(int(time.time() * 1000))
                e["title"] = str(e.get("title", "Seed")) + " (copy)"
            self._upsert_library_entry(e)
            added += 1
        self.status_var.set("Imported " + str(added) + " library seed(s)")

    def _scene_payload(self) -> dict:
        return {
            "scene": self.scene_var.get(),
            "bg": [10, 12, 16],
            "grid_cell": max(1, int(self.cell_size_var.get())),
            "layer_defs": self.layer_defs,
            "active_layer_id": self.active_layer_id,
            "items": self.items,
        }

    def _seed_checksum(self, data: bytes) -> str:
        c = 0
        for b in data:
            c = (c + int(b)) & 0xFFFF
        return hex(c)[2:].upper().rjust(4, "0")

    def _encode_seed(self, prefix: str, payload: dict) -> str:
        raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        body = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
        chk = self._seed_checksum(raw)
        return prefix + "-" + body + "-" + chk

    def _decode_seed(self, prefix: str, seed: str) -> dict | None:
        s = str(seed or "").strip()
        marker = prefix + "-"
        if not s.startswith(marker):
            return None
        rest = s[len(marker):]
        parts = rest.rsplit("-", 1)
        if len(parts) != 2:
            return None
        body, chk = parts[0], parts[1].upper()
        pad = "=" * ((4 - (len(body) % 4)) % 4)
        try:
            raw = base64.urlsafe_b64decode((body + pad).encode("ascii"))
            if self._seed_checksum(raw) != chk:
                return None
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return None

    def _build_scene_seed(self, payload: dict) -> str:
        return self._encode_seed("PLC", payload)

    def _load_scene_seed_db(self) -> None:
        self.scene_seed_db = {}
        if not SCENE_SEEDS_PATH.exists():
            return
        try:
            data = json.loads(SCENE_SEEDS_PATH.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(k, str) and isinstance(v, str):
                    self.scene_seed_db[k] = v

    def _save_scene_seed_db(self) -> None:
        SCENE_SEEDS_PATH.parent.mkdir(parents=True, exist_ok=True)
        SCENE_SEEDS_PATH.write_text(json.dumps(self.scene_seed_db, indent=2), encoding="utf-8")

    def _set_place_seed_for_current_scene(self) -> None:
        seed = self.scene_seed_db.get(self.scene_var.get(), "")
        self.place_seed_var.set(seed)
        if seed:
            self.place_seed_info_var.set("Share this code to recreate scene: " + self.scene_var.get())
        else:
            self.place_seed_info_var.set("No place seed yet")

    def _generate_scene_seed_current(self) -> None:
        payload = self._scene_payload()
        seed = self._build_scene_seed(payload)
        scene = payload.get("scene", self.scene_var.get())
        self.scene_seed_db[scene] = seed
        self._save_scene_seed_db()
        self._upsert_library_entry(
            {
                "seed_code": seed,
                "kind": "place",
                "title": "Place " + scene,
                "tags": ["place", scene],
                "meta": {"scene": scene, "dependencies": self._extract_place_dependencies(seed)},
            }
        )
        self.place_seed_var.set(seed)
        self.place_seed_info_var.set("Generated place seed for " + scene)
        self.status_var.set("Generated scene seed")

    def _apply_scene_seed_payload(self, payload: dict) -> None:
        scene = payload.get("scene", self.scene_var.get())
        if scene in EDITABLE_SCENES:
            self.scene_var.set(scene)
        defs = payload.get("layer_defs", [{"id": "base", "name": "Base", "visible": True, "locked": False}])
        if not isinstance(defs, list) or not defs:
            defs = [{"id": "base", "name": "Base", "visible": True, "locked": False}]
        has_base = any(str(d.get("id", "")) == "base" for d in defs if isinstance(d, dict))
        if not has_base:
            defs = [{"id": "base", "name": "Base", "visible": True, "locked": False}] + defs
        self.layer_defs = [d for d in defs if isinstance(d, dict)]
        self.active_layer_id = str(payload.get("active_layer_id", "base"))
        if self.active_layer_id not in self._layer_def_map():
            self.active_layer_id = "base"
        self.items = payload.get("items", [])
        self.cell_size_var.set(max(1, int(payload.get("grid_cell", self.cell_size_var.get()))))
        self.selected_indices.clear()
        self.selected_index = None
        self.undo_stack.clear()
        self.redo_stack.clear()
        self._render_canvas()

    def _load_scene_seed_from_entry(self) -> None:
        seed = self.place_seed_var.get().strip()
        payload = self._decode_seed("PLC", seed)
        if not payload:
            self.place_seed_info_var.set("Invalid place seed")
            return
        scene = payload.get("scene", self.scene_var.get())
        self.scene_seed_db[scene] = seed
        self._save_scene_seed_db()
        self._apply_scene_seed_payload(payload)
        self.place_seed_info_var.set("Loaded place seed for " + scene)
        self.status_var.set("Loaded scene seed")

    def _copy_place_seed(self) -> None:
        seed = self.place_seed_var.get().strip()
        if not seed:
            self.place_seed_info_var.set("No place seed to copy")
            return
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(seed)
            self.place_seed_info_var.set("Seed copied to clipboard")
        except Exception:
            self.place_seed_info_var.set("Clipboard unavailable")

    def _generate_all_scene_seeds(self) -> None:
        count = 0
        for scene in SCENE_NAMES:
            f = LAYOUTS / (scene + ".json")
            if not f.exists():
                continue
            try:
                payload = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue
            payload["scene"] = scene
            self.scene_seed_db[scene] = self._build_scene_seed(payload)
            count += 1
        self._save_scene_seed_db()
        self._set_place_seed_for_current_scene()
        self.place_seed_info_var.set("Generated " + str(count) + " scene seed(s)")

    def _export_seed_pack(self) -> None:
        fp = filedialog.asksaveasfilename(
            title="Export Place Seed Pack",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialdir=str(LAYOUTS),
            initialfile="place_seed_pack.json",
        )
        if not fp:
            return
        payload = {
            "type": "guildsim_place_seed_pack",
            "version": 1,
            "seeds": self.scene_seed_db,
        }
        Path(fp).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self.status_var.set("Exported seed pack")

    def _import_seed_pack(self) -> None:
        fp = filedialog.askopenfilename(
            title="Import Place Seed Pack",
            filetypes=[("JSON files", "*.json")],
            initialdir=str(LAYOUTS),
        )
        if not fp:
            return
        try:
            payload = json.loads(Path(fp).read_text(encoding="utf-8"))
        except Exception:
            self.status_var.set("Invalid seed pack")
            return

        seeds = payload.get("seeds", {}) if isinstance(payload, dict) else {}
        if not isinstance(seeds, dict):
            self.status_var.set("Invalid seed pack")
            return

        added = 0
        for k, v in seeds.items():
            if isinstance(k, str) and isinstance(v, str) and self._decode_seed("PLC", v):
                self.scene_seed_db[k] = v
                added += 1
        self._save_scene_seed_db()
        self._set_place_seed_for_current_scene()
        self.status_var.set("Imported " + str(added) + " seed(s)")

    def _snapshot(self) -> str:
        return json.dumps(self.items, sort_keys=True)

    def _push_undo(self) -> None:
        self.undo_stack.append(self._snapshot())
        if len(self.undo_stack) > 200:
            self.undo_stack = self.undo_stack[-200:]
        self.redo_stack.clear()

    def _restore_snapshot(self, snap: str) -> None:
        self.items = json.loads(snap)
        self.selected_indices.clear()
        self.selected_index = None
        self._render_canvas()

    def _undo(self) -> None:
        if not self.undo_stack:
            self.status_var.set("Nothing to undo")
            return
        self.redo_stack.append(self._snapshot())
        snap = self.undo_stack.pop()
        self._restore_snapshot(snap)
        self.status_var.set("Undo")

    def _redo(self) -> None:
        if not self.redo_stack:
            self.status_var.set("Nothing to redo")
            return
        self.undo_stack.append(self._snapshot())
        snap = self.redo_stack.pop()
        self._restore_snapshot(snap)
        self.status_var.set("Redo")

    def _apply_zoom_var(self) -> None:
        self._set_zoom(self.zoom_var.get())

    def _apply_view_mode(self) -> None:
        self._set_zoom(self.zoom_var.get())

    def _set_zoom(self, zoom: int) -> None:
        zoom = max(MIN_ZOOM, min(MAX_ZOOM, int(zoom)))
        self.zoom_var.set(zoom)
        self.canvas.config(width=self._canvas_width_px(), height=self._canvas_height_px())
        self._render_canvas()

    def _view_is_perspective(self) -> bool:
        return self.view_mode_var.get().strip().lower() == "perspective"

    def _perspective_params(self) -> tuple[float, float]:
        skew = float(self.perspective_skew_var.get())
        y_scale = float(self.perspective_scale_var.get())
        skew = max(0.0, min(1.0, skew))
        y_scale = max(0.25, min(1.0, y_scale))
        return skew, y_scale

    def _canvas_width_px(self) -> int:
        z = max(1, int(self.zoom_var.get()))
        if not self._view_is_perspective():
            return W * z
        skew, _ys = self._perspective_params()
        return int((W + H * skew) * z)

    def _canvas_height_px(self) -> int:
        z = max(1, int(self.zoom_var.get()))
        if not self._view_is_perspective():
            return H * z
        _skew, ys = self._perspective_params()
        return int(H * ys * z)

    def _scene_to_canvas(self, x: float, y: float) -> tuple[float, float]:
        z = max(1, int(self.zoom_var.get()))
        if not self._view_is_perspective():
            return x * z, y * z
        skew, ys = self._perspective_params()
        return (x + y * skew) * z, (y * ys) * z

    def _canvas_to_scene(self, x_px: float, y_px: float) -> tuple[float, float]:
        z = max(1, int(self.zoom_var.get()))
        if not self._view_is_perspective():
            return x_px / z, y_px / z
        skew, ys = self._perspective_params()
        sy = y_px / (z * ys)
        sx = (x_px / z) - (sy * skew)
        return sx, sy

    def _on_mouse_wheel(self, event) -> None:
        delta = 1 if event.delta > 0 else -1
        self._set_zoom(self.zoom_var.get() + delta)

    def _scan_assets(self) -> None:
        pools = [ASSETS / "UI", ASSETS / "Icons", ASSETS / "Tilesets", ASSETS / "backgrounds", ASSETS / "Enemies", ASSETS / "characters"]
        found: list[Path] = []
        for base in pools:
            if not base.exists():
                continue
            found.extend([p for p in base.rglob("*.png") if p.is_file()])
        self.sprites = sorted(found)

    def _refresh_tree(self) -> None:
        self.item_rel_by_iid.clear()
        self.iid_by_rel.clear()
        self.tree.delete(*self.tree.get_children())

        q = self.search_var.get().strip().lower()
        dirs: dict[str, str] = {}

        for p in self.sprites:
            rel = p.relative_to(ASSETS).as_posix()
            if q and q not in rel.lower() and q not in p.stem.lower():
                continue

            parts = rel.split("/")
            parent = ""
            path_accum = []
            for d in parts[:-1]:
                path_accum.append(d)
                key = "/".join(path_accum)
                if key not in dirs:
                    iid = self.tree.insert(parent, "end", text=d, open=True)
                    dirs[key] = iid
                parent = dirs[key]

            iid = self.tree.insert(parent, "end", text=parts[-1])
            self.item_rel_by_iid[iid] = rel
            self.iid_by_rel[rel] = iid

    def _scene_file(self) -> Path:
        return LAYOUTS / f"{self.scene_var.get()}.json"

    def _resolve_image(self, rel: str) -> Image.Image | None:
        if rel in self.image_cache:
            return self.image_cache[rel]
        path = ASSETS / rel
        if not path.exists():
            return None
        img = Image.open(path).convert("RGBA")
        self.image_cache[rel] = img
        return img

    def _clamp_grid(self, x: int, y: int) -> tuple[int, int]:
        if not self.snap_var.get():
            return max(0, min(W - 1, x)), max(0, min(H - 1, y))
        cell = max(1, int(self.cell_size_var.get()))
        gx = (x // cell) * cell
        gy = (y // cell) * cell
        return max(0, min(W - 1, gx)), max(0, min(H - 1, gy))

    def _event_to_scene(self, event) -> tuple[int, int]:
        sx, sy = self._canvas_to_scene(float(event.x), float(event.y))
        px = int(sx)
        py = int(sy)
        return max(0, min(W - 1, px)), max(0, min(H - 1, py))

    def _render_grid(self) -> None:
        if not self.show_grid_var.get():
            return
        cell = max(1, int(self.cell_size_var.get()))
        color = "#1f2933"
        for x in range(0, W + 1, cell):
            x0, y0 = self._scene_to_canvas(float(x), 0.0)
            x1, y1 = self._scene_to_canvas(float(x), float(H))
            self.canvas.create_line(x0, y0, x1, y1, fill=color)
        for y in range(0, H + 1, cell):
            x0, y0 = self._scene_to_canvas(0.0, float(y))
            x1, y1 = self._scene_to_canvas(float(W), float(y))
            self.canvas.create_line(x0, y0, x1, y1, fill=color)

    def _refresh_layers(self) -> None:
        self._refresh_layer_defs_list()
        self.layers_list.delete(0, tk.END)
        for i, it in enumerate(self.items):
            t = it.get("type", "sprite")
            if t == "sprite":
                label = Path(it.get("path", "sprite")).name
                sx = int(it.get("src_x", 0))
                sy = int(it.get("src_y", 0))
                sw = int(it.get("src_w", it.get("w", 0)))
                sh = int(it.get("src_h", it.get("h", 0)))
                self._ensure_item_layer(it)
                lid = str(it.get("layer_id", "base"))
                label = f"{self._layer_name(lid)}:{label} [{sx},{sy},{sw},{sh}]"
            elif t == "text":
                label = f"text:{it.get('text', '')[:14]}"
            else:
                label = t
            self.layers_list.insert(tk.END, f"{i:02d} {label}")

        self.layers_list.selection_clear(0, tk.END)
        for idx in sorted(self.selected_indices):
            if 0 <= idx < len(self.items):
                self.layers_list.selection_set(idx)

    def _layer_def_map(self) -> dict[str, dict]:
        return {str(ld.get("id", "base")): ld for ld in self.layer_defs}

    def _ensure_item_layer(self, it: dict) -> None:
        lid = str(it.get("layer_id", "")).strip() or "base"
        if lid not in self._layer_def_map():
            lid = "base"
        it["layer_id"] = lid

    def _layer_is_visible(self, layer_id: str) -> bool:
        ld = self._layer_def_map().get(layer_id)
        return bool(ld.get("visible", True)) if ld else True

    def _layer_is_locked(self, layer_id: str) -> bool:
        ld = self._layer_def_map().get(layer_id)
        return bool(ld.get("locked", False)) if ld else False

    def _layer_name(self, layer_id: str) -> str:
        ld = self._layer_def_map().get(layer_id)
        return str(ld.get("name", layer_id)) if ld else layer_id

    def _refresh_layer_defs_list(self) -> None:
        if not hasattr(self, "layer_defs_list"):
            return
        self.layer_defs_list.delete(0, tk.END)
        for i, ld in enumerate(self.layer_defs):
            lid = str(ld.get("id", "base"))
            name = str(ld.get("name", lid))
            vis = "V" if bool(ld.get("visible", True)) else "H"
            lock = "L" if bool(ld.get("locked", False)) else "-"
            marker = "*" if lid == self.active_layer_id else " "
            self.layer_defs_list.insert(tk.END, f"{marker} {i:02d} [{vis}/{lock}] {name}")

        self.layer_defs_list.selection_clear(0, tk.END)
        for i, ld in enumerate(self.layer_defs):
            if str(ld.get("id", "")) == self.active_layer_id:
                self.layer_defs_list.selection_set(i)
                break

    def _selected_layer_def_indices(self) -> list[int]:
        if not hasattr(self, "layer_defs_list"):
            return []
        return [int(i) for i in self.layer_defs_list.curselection() if 0 <= int(i) < len(self.layer_defs)]

    def _on_layer_def_select(self) -> None:
        sel = self._selected_layer_def_indices()
        if not sel:
            return
        i = sel[0]
        self.active_layer_id = str(self.layer_defs[i].get("id", "base"))
        self.status_var.set("Active layer: " + self._layer_name(self.active_layer_id))
        self._refresh_layer_defs_list()

    def _new_layer(self) -> None:
        self.layer_counter += 1
        lid = "layer_" + str(self.layer_counter)
        self.layer_defs.append({"id": lid, "name": "Layer " + str(self.layer_counter), "visible": True, "locked": False})
        self.active_layer_id = lid
        self._refresh_layer_defs_list()
        self.status_var.set("Created layer")

    def _duplicate_layers(self) -> None:
        sel = self._selected_layer_def_indices()
        if not sel:
            self.status_var.set("Select layer(s) to duplicate")
            return
        new_ids: list[str] = []
        for i in sel:
            src = self.layer_defs[i]
            self.layer_counter += 1
            lid = "layer_" + str(self.layer_counter)
            self.layer_defs.append(
                {
                    "id": lid,
                    "name": str(src.get("name", "Layer")) + " Copy",
                    "visible": bool(src.get("visible", True)),
                    "locked": bool(src.get("locked", False)),
                }
            )
            new_ids.append(lid)
        if new_ids:
            self.active_layer_id = new_ids[-1]
        self._refresh_layer_defs_list()
        self.status_var.set("Duplicated " + str(len(sel)) + " layer(s)")

    def _remove_layers(self) -> None:
        sel = self._selected_layer_def_indices()
        if not sel:
            self.status_var.set("Select layer(s) to remove")
            return
        remove_ids = {str(self.layer_defs[i].get("id", "")) for i in sel if str(self.layer_defs[i].get("id", "")) != "base"}
        if not remove_ids:
            self.status_var.set("Base layer cannot be removed")
            return

        self.layer_defs = [ld for ld in self.layer_defs if str(ld.get("id", "")) not in remove_ids]
        for it in self.items:
            self._ensure_item_layer(it)
            if str(it.get("layer_id", "base")) in remove_ids:
                it["layer_id"] = "base"

        if self.active_layer_id in remove_ids:
            self.active_layer_id = "base"
        self._refresh_layer_defs_list()
        self._render_canvas()
        self.status_var.set("Removed " + str(len(remove_ids)) + " layer(s)")

    def _toggle_layers_visibility(self) -> None:
        sel = self._selected_layer_def_indices()
        if not sel:
            self.status_var.set("Select layer(s) to toggle visibility")
            return
        for i in sel:
            ld = self.layer_defs[i]
            ld["visible"] = not bool(ld.get("visible", True))
        self._refresh_layer_defs_list()
        self._render_canvas()
        self.status_var.set("Layer visibility toggled")

    def _toggle_layers_lock(self) -> None:
        sel = self._selected_layer_def_indices()
        if not sel:
            self.status_var.set("Select layer(s) to toggle lock")
            return
        for i in sel:
            ld = self.layer_defs[i]
            ld["locked"] = not bool(ld.get("locked", False))
        self._refresh_layer_defs_list()
        self.status_var.set("Layer lock toggled")

    def _assign_selected_to_active_layer(self) -> None:
        if not self.selected_indices:
            self.status_var.set("No selected objects")
            return
        if self.active_layer_id not in self._layer_def_map():
            self.active_layer_id = "base"
        self._push_undo()
        count = 0
        for i in sorted(self.selected_indices):
            if 0 <= i < len(self.items):
                self.items[i]["layer_id"] = self.active_layer_id
                count += 1
        self._render_canvas()
        self.status_var.set("Assigned " + str(count) + " object(s) to " + self._layer_name(self.active_layer_id))

    def _selected_bounds(self) -> tuple[float, float, float, float] | None:
        if not self.selected_indices:
            return None
        xs: list[float] = []
        ys: list[float] = []
        for i in self.selected_indices:
            if not (0 <= i < len(self.items)):
                continue
            it = self.items[i]
            t = it.get("type", "sprite")
            if t == "line":
                x1 = float(it.get("x", 0))
                y1 = float(it.get("y", 0))
                x2 = float(it.get("x2", x1 + it.get("w", 1)))
                y2 = float(it.get("y2", y1 + it.get("h", 1)))
                xs.extend([x1, x2])
                ys.extend([y1, y2])
            else:
                x = float(it.get("x", 0))
                y = float(it.get("y", 0))
                w = float(max(1, int(it.get("w", 1))))
                h = float(max(1, int(it.get("h", 1))))
                xs.extend([x, x + w])
                ys.extend([y, y + h])
        if not xs:
            return None
        return min(xs), min(ys), max(xs), max(ys)

    def _handle_positions(self, bounds: tuple[float, float, float, float]) -> dict[str, tuple[float, float]]:
        x0, y0, x1, y1 = bounds
        xm = (x0 + x1) / 2.0
        ym = (y0 + y1) / 2.0
        return {
            "nw": (x0, y0),
            "n": (xm, y0),
            "ne": (x1, y0),
            "e": (x1, ym),
            "se": (x1, y1),
            "s": (xm, y1),
            "sw": (x0, y1),
            "w": (x0, ym),
        }

    def _hit_transform_handle(self, x: int, y: int) -> str | None:
        bounds = self._selected_bounds()
        if bounds is None:
            return None
        tol = max(2, int(self.cell_size_var.get()) // 2)
        for name, (hx, hy) in self._handle_positions(bounds).items():
            if abs(x - hx) <= tol and abs(y - hy) <= tol:
                return name
        return None

    def _opposite_handle(self, name: str) -> str:
        pairs = {"nw": "se", "n": "s", "ne": "sw", "e": "w", "se": "nw", "s": "n", "sw": "ne", "w": "e"}
        return pairs.get(name, "se")

    def _rotation_handle_pos(self, bounds: tuple[float, float, float, float]) -> tuple[float, float]:
        x0, y0, x1, _y1 = bounds
        return ((x0 + x1) / 2.0, y0 - max(6, int(self.cell_size_var.get())))

    def _hit_rotation_handle(self, x: int, y: int) -> bool:
        bounds = self._selected_bounds()
        if bounds is None:
            return False
        hx, hy = self._rotation_handle_pos(bounds)
        tol = max(3, int(self.cell_size_var.get()) // 2)
        return abs(x - hx) <= tol and abs(y - hy) <= tol

    def _rotate_point_any(self, x: float, y: float, px: float, py: float, angle_deg: float) -> tuple[float, float]:
        r = math.radians(angle_deg)
        cs = math.cos(r)
        sn = math.sin(r)
        dx = x - px
        dy = y - py
        return (px + dx * cs - dy * sn, py + dx * sn + dy * cs)

    def _apply_rotation_to_item(self, src: dict, px: float, py: float, angle_deg: float) -> dict:
        out = json.loads(json.dumps(src))
        t = out.get("type", "sprite")
        if t == "line":
            x1 = float(out.get("x", 0))
            y1 = float(out.get("y", 0))
            x2 = float(out.get("x2", x1 + out.get("w", 1)))
            y2 = float(out.get("y2", y1 + out.get("h", 1)))
            nx1, ny1 = self._rotate_point_any(x1, y1, px, py, angle_deg)
            nx2, ny2 = self._rotate_point_any(x2, y2, px, py, angle_deg)
            out["x"] = int(round(nx1))
            out["y"] = int(round(ny1))
            out["x2"] = int(round(nx2))
            out["y2"] = int(round(ny2))
            out["w"] = int(round(nx2 - nx1))
            out["h"] = int(round(ny2 - ny1))
            return out

        x = float(out.get("x", 0))
        y = float(out.get("y", 0))
        w = float(max(1, int(out.get("w", 1))))
        h = float(max(1, int(out.get("h", 1))))
        corners = [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]
        rc = [self._rotate_point_any(cx, cy, px, py, angle_deg) for cx, cy in corners]
        xs = [p[0] for p in rc]
        ys = [p[1] for p in rc]
        min_x, min_y = int(round(min(xs))), int(round(min(ys)))
        max_x, max_y = int(round(max(xs))), int(round(max(ys)))
        out["x"] = min_x
        out["y"] = min_y
        out["w"] = max(1, max_x - min_x)
        out["h"] = max(1, max_y - min_y)
        if t == "sprite":
            out["rot"] = (int(src.get("rot", 0)) + int(round(angle_deg))) % 360
        return out

    def _rotate_selected_drag(self, px: int, py: int) -> None:
        if not self.rotate_start_items:
            return
        pvx, pvy = self.rotate_pivot
        a0 = self.rotate_start_angle
        a1 = math.degrees(math.atan2(py - pvy, px - pvx))
        delta = a1 - a0
        for i, src in self.rotate_start_items.items():
            if 0 <= i < len(self.items):
                self.items[i] = self._apply_rotation_to_item(src, pvx, pvy, delta)
        self._update_prop_fields()
        self._render_canvas()

    def _apply_scale_to_item(self, src: dict, px: float, py: float, sx: float, sy: float) -> dict:
        out = json.loads(json.dumps(src))
        t = out.get("type", "sprite")
        if t == "line":
            x1 = float(out.get("x", 0))
            y1 = float(out.get("y", 0))
            x2 = float(out.get("x2", x1 + out.get("w", 1)))
            y2 = float(out.get("y2", y1 + out.get("h", 1)))
            nx1 = px + (x1 - px) * sx
            ny1 = py + (y1 - py) * sy
            nx2 = px + (x2 - px) * sx
            ny2 = py + (y2 - py) * sy
            out["x"] = int(round(nx1))
            out["y"] = int(round(ny1))
            out["x2"] = int(round(nx2))
            out["y2"] = int(round(ny2))
            out["w"] = int(round(nx2 - nx1))
            out["h"] = int(round(ny2 - ny1))
            return out

        x = float(out.get("x", 0))
        y = float(out.get("y", 0))
        w = float(max(1, int(out.get("w", 1))))
        h = float(max(1, int(out.get("h", 1))))

        corners = [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]
        scaled = [(px + (cx - px) * sx, py + (cy - py) * sy) for cx, cy in corners]
        xs = [p[0] for p in scaled]
        ys = [p[1] for p in scaled]
        min_x = int(round(min(xs)))
        min_y = int(round(min(ys)))
        max_x = int(round(max(xs)))
        max_y = int(round(max(ys)))
        out["x"] = min_x
        out["y"] = min_y
        out["w"] = max(1, max_x - min_x)
        out["h"] = max(1, max_y - min_y)
        return out

    def _scale_selected_with_handle(self, px: int, py: int) -> None:
        if not self.scale_handle or not self.scale_start_items:
            return
        hx0, hy0 = self.scale_start_handle_pos
        pvx, pvy = self.scale_pivot

        sx = 1.0
        sy = 1.0
        if self.scale_handle in ("nw", "w", "sw", "e", "ne", "se"):
            denom_x = hx0 - pvx
            if abs(denom_x) > 1e-6:
                sx = (px - pvx) / denom_x
        if self.scale_handle in ("nw", "n", "ne", "s", "sw", "se"):
            denom_y = hy0 - pvy
            if abs(denom_y) > 1e-6:
                sy = (py - pvy) / denom_y

        if self.scale_handle in ("n", "s"):
            sx = 1.0
        if self.scale_handle in ("e", "w"):
            sy = 1.0

        sx = max(0.05, sx)
        sy = max(0.05, sy)

        for i, src in self.scale_start_items.items():
            if not (0 <= i < len(self.items)):
                continue
            self.items[i] = self._apply_scale_to_item(src, pvx, pvy, sx, sy)

        self._update_prop_fields()
        self._render_canvas()

    def _get_transform_pivot(self) -> tuple[float, float]:
        mode = self.pivot_mode_var.get().strip().lower()
        bounds = self._selected_bounds()
        if mode == "custom":
            return float(self.pivot_x_var.get()), float(self.pivot_y_var.get())
        if bounds is None:
            return float(self.pivot_x_var.get()), float(self.pivot_y_var.get())
        x0, y0, x1, y1 = bounds
        if mode == "topleft":
            return x0, y0
        return (x0 + x1) / 2.0, (y0 + y1) / 2.0

    def _rotate_point(self, x: float, y: float, px: float, py: float, angle: int) -> tuple[float, float]:
        a = angle % 360
        dx = x - px
        dy = y - py
        if a == 90:
            return px + dy, py - dx
        if a == 180:
            return px - dx, py - dy
        if a == 270:
            return px - dy, py + dx
        return x, y

    def _transform_rect_rotate(self, it: dict, px: float, py: float, angle: int) -> None:
        x = float(it.get("x", 0))
        y = float(it.get("y", 0))
        w = float(max(1, int(it.get("w", 1))))
        h = float(max(1, int(it.get("h", 1))))
        corners = [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]
        rc = [self._rotate_point(cx, cy, px, py, angle) for cx, cy in corners]
        xs = [p[0] for p in rc]
        ys = [p[1] for p in rc]
        min_x, min_y = int(round(min(xs))), int(round(min(ys)))
        max_x, max_y = int(round(max(xs))), int(round(max(ys)))
        it["x"] = min_x
        it["y"] = min_y
        it["w"] = max(1, max_x - min_x)
        it["h"] = max(1, max_y - min_y)

    def _rotate_selected(self, angle: int) -> None:
        if not self.selected_indices:
            self.status_var.set("No selected item")
            return
        angle = angle % 360
        if angle not in (90, 180, 270):
            return

        self._push_undo()
        px, py = self._get_transform_pivot()

        for i in sorted(self.selected_indices):
            if not (0 <= i < len(self.items)):
                continue
            it = self.items[i]
            if it.get("type") == "line":
                x1 = float(it.get("x", 0))
                y1 = float(it.get("y", 0))
                x2 = float(it.get("x2", x1 + it.get("w", 1)))
                y2 = float(it.get("y2", y1 + it.get("h", 1)))
                nx1, ny1 = self._rotate_point(x1, y1, px, py, angle)
                nx2, ny2 = self._rotate_point(x2, y2, px, py, angle)
                it["x"] = int(round(nx1))
                it["y"] = int(round(ny1))
                it["x2"] = int(round(nx2))
                it["y2"] = int(round(ny2))
                it["w"] = int(round(nx2 - nx1))
                it["h"] = int(round(ny2 - ny1))
            else:
                self._transform_rect_rotate(it, px, py, angle)
                if it.get("type") == "sprite":
                    it["rot"] = (int(it.get("rot", 0)) + angle) % 360

        self._update_prop_fields()
        self._render_canvas()
        self.status_var.set(f"Rotated {len(self.selected_indices)} item(s)")

    def _flip_selected(self, axis: str) -> None:
        if not self.selected_indices:
            self.status_var.set("No selected item")
            return
        self._push_undo()
        px, py = self._get_transform_pivot()

        for i in sorted(self.selected_indices):
            if not (0 <= i < len(self.items)):
                continue
            it = self.items[i]
            t = it.get("type", "sprite")
            if t == "line":
                x1 = float(it.get("x", 0))
                y1 = float(it.get("y", 0))
                x2 = float(it.get("x2", x1 + it.get("w", 1)))
                y2 = float(it.get("y2", y1 + it.get("h", 1)))
                if axis == "h":
                    x1 = 2 * px - x1
                    x2 = 2 * px - x2
                else:
                    y1 = 2 * py - y1
                    y2 = 2 * py - y2
                it["x"] = int(round(x1))
                it["y"] = int(round(y1))
                it["x2"] = int(round(x2))
                it["y2"] = int(round(y2))
                it["w"] = int(round(x2 - x1))
                it["h"] = int(round(y2 - y1))
                continue

            x = float(it.get("x", 0))
            y = float(it.get("y", 0))
            w = float(max(1, int(it.get("w", 1))))
            h = float(max(1, int(it.get("h", 1))))
            if axis == "h":
                nx = 2 * px - (x + w)
                it["x"] = int(round(nx))
                if t == "sprite":
                    it["flip_x"] = not bool(it.get("flip_x", False))
            else:
                ny = 2 * py - (y + h)
                it["y"] = int(round(ny))
                if t == "sprite":
                    it["flip_y"] = not bool(it.get("flip_y", False))

        self._update_prop_fields()
        self._show_mirror_guide(axis)
        self._render_canvas()
        self.status_var.set(f"Flipped {len(self.selected_indices)} item(s)")

    def _show_mirror_guide(self, axis: str) -> None:
        self.mirror_guide_axis = axis if axis in ("h", "v") else None
        if self._mirror_guide_job is not None:
            try:
                self.root.after_cancel(self._mirror_guide_job)
            except Exception:
                pass
            self._mirror_guide_job = None
        if self.mirror_guide_axis is not None:
            self._mirror_guide_job = self.root.after(1200, self._clear_mirror_guide)

    def _clear_mirror_guide(self) -> None:
        self.mirror_guide_axis = None
        self._mirror_guide_job = None
        self._render_canvas()

    def _tile_cell_key(self, x: int, y: int) -> tuple[int, int]:
        cell = max(1, int(self.cell_size_var.get()))
        return (x // cell) * cell, (y // cell) * cell

    def _tile_index_map(self) -> dict[tuple[int, int], int]:
        m: dict[tuple[int, int], int] = {}
        for i, it in enumerate(self.items):
            self._ensure_item_layer(it)
            if it.get("type") != "sprite" or it.get("layer") != "tilemap":
                continue
            if str(it.get("layer_id", "base")) != self.active_layer_id:
                continue
            x = int(it.get("x", 0))
            y = int(it.get("y", 0))
            m[self._tile_cell_key(x, y)] = i
        return m

    def _selected_tile_key(self) -> tuple[str, int, int, int, int] | None:
        rel = self._selected_rel_from_tree()
        if not rel:
            return None
        img = self._resolve_image(rel)
        if img is None:
            return None
        iw, ih = img.size
        cell = max(1, int(self.cell_size_var.get()))

        sx, sy, sw, sh = 0, 0, iw, ih
        if iw > cell or ih > cell:
            cx, cy = self.sheet_selected
            cols = max(1, iw // cell)
            rows = max(1, ih // cell)
            cx = max(0, min(cols - 1, cx))
            cy = max(0, min(rows - 1, cy))
            sx = cx * cell
            sy = cy * cell
            sw = min(cell, iw - sx)
            sh = min(cell, ih - sy)
        return rel, sx, sy, sw, sh

    def _tile_signature(self, item: dict | None) -> tuple | None:
        if not item:
            return None
        if item.get("type") != "sprite":
            return (item.get("type"),)
        return (
            "sprite",
            item.get("path", ""),
            int(item.get("src_x", 0)),
            int(item.get("src_y", 0)),
            int(item.get("src_w", item.get("w", 1))),
            int(item.get("src_h", item.get("h", 1))),
            int(item.get("rot", 0)) % 360,
            bool(item.get("flip_x", False)),
            bool(item.get("flip_y", False)),
        )

    def _apply_tile_brush(self, x: int, y: int) -> None:
        cell = max(1, int(self.cell_size_var.get()))
        cx, cy = self._tile_cell_key(x, y)
        b = max(1, int(self.brush_size_var.get()))
        half = b // 2

        tile_key = self._selected_tile_key()
        if not self.tile_eraser_var.get() and tile_key is None:
            self.status_var.set("Select a sprite tile first")
            return

        idx_map = self._tile_index_map()
        rel = tile_key[0] if tile_key else ""
        sx = tile_key[1] if tile_key else 0
        sy = tile_key[2] if tile_key else 0
        sw = tile_key[3] if tile_key else cell
        sh = tile_key[4] if tile_key else cell

        for oy in range(-half, half + 1):
            for ox in range(-half, half + 1):
                tx = max(0, min(W - cell, cx + ox * cell))
                ty = max(0, min(H - cell, cy + oy * cell))
                old_i = idx_map.get((tx, ty))

                if self.tile_eraser_var.get():
                    if old_i is not None and 0 <= old_i < len(self.items):
                        self.items.pop(old_i)
                        idx_map = self._tile_index_map()
                    continue

                if old_i is not None and 0 <= old_i < len(self.items):
                    self.items.pop(old_i)
                    idx_map = self._tile_index_map()

                self.items.append(
                    {
                        "type": "sprite",
                        "layer_id": self.active_layer_id,
                        "layer": "tilemap",
                        "path": rel,
                        "x": tx,
                        "y": ty,
                        "w": max(1, sw),
                        "h": max(1, sh),
                        "src_x": sx,
                        "src_y": sy,
                        "src_w": sw,
                        "src_h": sh,
                        "rot": 0,
                        "flip_x": False,
                        "flip_y": False,
                    }
                )
                idx_map[(tx, ty)] = len(self.items) - 1

    def _tile_flood_fill(self, x: int, y: int) -> None:
        cell = max(1, int(self.cell_size_var.get()))
        start = self._tile_cell_key(x, y)
        idx_map = self._tile_index_map()
        target_item = self.items[idx_map[start]] if start in idx_map and 0 <= idx_map[start] < len(self.items) else None
        target_sig = self._tile_signature(target_item)

        tile_key = self._selected_tile_key()
        if not self.tile_eraser_var.get() and tile_key is None:
            self.status_var.set("Select a sprite tile first")
            return

        if (not self.tile_eraser_var.get()) and tile_key is not None:
            rel, sx, sy, sw, sh = tile_key
            replacement_sig = ("sprite", rel, sx, sy, sw, sh, 0, False, False)
            if replacement_sig == target_sig:
                return

        stack = [start]
        seen: set[tuple[int, int]] = set()
        self._push_undo()

        while stack:
            cx, cy = stack.pop()
            if (cx, cy) in seen:
                continue
            seen.add((cx, cy))

            cur_i = idx_map.get((cx, cy))
            cur_item = self.items[cur_i] if cur_i is not None and 0 <= cur_i < len(self.items) else None
            if self._tile_signature(cur_item) != target_sig:
                continue

            if self.tile_eraser_var.get():
                if cur_i is not None and 0 <= cur_i < len(self.items):
                    self.items.pop(cur_i)
                    idx_map = self._tile_index_map()
            else:
                rel, sx, sy, sw, sh = tile_key  # type: ignore[misc]
                if cur_i is not None and 0 <= cur_i < len(self.items):
                    self.items.pop(cur_i)
                    idx_map = self._tile_index_map()
                self.items.append(
                    {
                        "type": "sprite",
                        "layer_id": self.active_layer_id,
                        "layer": "tilemap",
                        "path": rel,
                        "x": cx,
                        "y": cy,
                        "w": max(1, sw),
                        "h": max(1, sh),
                        "src_x": sx,
                        "src_y": sy,
                        "src_w": sw,
                        "src_h": sh,
                        "rot": 0,
                        "flip_x": False,
                        "flip_y": False,
                    }
                )
                idx_map[(cx, cy)] = len(self.items) - 1

            for nx, ny in ((cx + cell, cy), (cx - cell, cy), (cx, cy + cell), (cx, cy - cell)):
                if 0 <= nx < W and 0 <= ny < H and (nx, ny) not in seen:
                    stack.append((nx, ny))

        self._render_canvas()
        self.status_var.set("Tilemap flood fill")

    def _render_canvas(self) -> None:
        z = int(self.zoom_var.get())
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, self._canvas_width_px(), self._canvas_height_px(), fill="#000", outline="")
        self._render_grid()
        self.tk_cache.clear()

        for i, it in enumerate(self.items):
            self._ensure_item_layer(it)
            if not self._layer_is_visible(str(it.get("layer_id", "base"))):
                continue
            t = it.get("type", "sprite")
            x = int(it.get("x", 0))
            y = int(it.get("y", 0))
            w = int(it.get("w", 8))
            h = int(it.get("h", 8))

            if t == "sprite":
                rel = it.get("path", "")
                img = self._resolve_image(rel)
                if img is not None:
                    sx = int(it.get("src_x", 0))
                    sy = int(it.get("src_y", 0))
                    sw = int(it.get("src_w", img.size[0]))
                    sh = int(it.get("src_h", img.size[1]))
                    crop = img.crop((sx, sy, sx + sw, sy + sh))
                    if bool(it.get("flip_x", False)):
                        crop = crop.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                    if bool(it.get("flip_y", False)):
                        crop = crop.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                    rot = int(it.get("rot", 0)) % 360
                    if rot:
                        crop = crop.rotate(-rot, expand=True, resample=Image.Resampling.NEAREST)
                    draw_h = h
                    if self._view_is_perspective():
                        _skew, ys = self._perspective_params()
                        draw_h = max(1, int(round(h * ys)))
                    view = crop.resize((max(1, w * z), max(1, draw_h * z)), Image.Resampling.NEAREST)
                    key = (
                        f"sprite:{i}:{rel}:{x}:{y}:{w}:{h}:{sx}:{sy}:{sw}:{sh}:"
                        f"{it.get('rot', 0)}:{it.get('flip_x', False)}:{it.get('flip_y', False)}:{z}"
                    )
                    self.tk_cache[key] = ImageTk.PhotoImage(view)
                    vx, vy = self._scene_to_canvas(float(x), float(y))
                    self.canvas.create_image(vx, vy, image=self.tk_cache[key], anchor="nw")
            elif t == "text":
                vx, vy = self._scene_to_canvas(float(x), float(y))
                self.canvas.create_text(vx, vy, text=it.get("text", "Text"), fill=it.get("color", "#ffffff"), anchor="nw")
            elif t == "line":
                x2 = int(it.get("x2", x + w))
                y2 = int(it.get("y2", y + h))
                sw = int(it.get("stroke", 1))
                vx1, vy1 = self._scene_to_canvas(float(x), float(y))
                vx2, vy2 = self._scene_to_canvas(float(x2), float(y2))
                self.canvas.create_line(vx1, vy1, vx2, vy2, fill=it.get("color", "#ffffff"), width=max(1, sw * z // 2))
            elif t == "rect":
                sw = int(it.get("stroke", 1))
                p1 = self._scene_to_canvas(float(x), float(y))
                p2 = self._scene_to_canvas(float(x + w), float(y))
                p3 = self._scene_to_canvas(float(x + w), float(y + h))
                p4 = self._scene_to_canvas(float(x), float(y + h))
                self.canvas.create_polygon(
                    p1[0], p1[1], p2[0], p2[1], p3[0], p3[1], p4[0], p4[1],
                    outline=it.get("color", "#ffffff"), fill="", width=max(1, sw * z // 2)
                )
            elif t == "char_marker":
                p1 = self._scene_to_canvas(float(x), float(y))
                p2 = self._scene_to_canvas(float(x + w), float(y))
                p3 = self._scene_to_canvas(float(x + w), float(y + h))
                p4 = self._scene_to_canvas(float(x), float(y + h))
                self.canvas.create_polygon(p1[0], p1[1], p2[0], p2[1], p3[0], p3[1], p4[0], p4[1], outline="#22cc22", fill="", width=2, dash=(4, 3))
                tx, ty = self._scene_to_canvas(float(x + 1), float(y + 1))
                self.canvas.create_text(tx, ty, text="CHAR", fill="#22cc22", anchor="nw")
            elif t == "enemy_marker":
                p1 = self._scene_to_canvas(float(x), float(y))
                p2 = self._scene_to_canvas(float(x + w), float(y))
                p3 = self._scene_to_canvas(float(x + w), float(y + h))
                p4 = self._scene_to_canvas(float(x), float(y + h))
                self.canvas.create_polygon(p1[0], p1[1], p2[0], p2[1], p3[0], p3[1], p4[0], p4[1], outline="#ff3333", fill="", width=2, dash=(4, 3))
                tx, ty = self._scene_to_canvas(float(x + 1), float(y + 1))
                self.canvas.create_text(tx, ty, text="ENEMY", fill="#ff3333", anchor="nw")

            if i in self.selected_indices:
                color = "#00c8ff" if i == self.selected_index else "#f6e05e"
                p1 = self._scene_to_canvas(float(x), float(y))
                p2 = self._scene_to_canvas(float(x + max(1, w)), float(y))
                p3 = self._scene_to_canvas(float(x + max(1, w)), float(y + max(1, h)))
                p4 = self._scene_to_canvas(float(x), float(y + max(1, h)))
                self.canvas.create_polygon(p1[0], p1[1], p2[0], p2[1], p3[0], p3[1], p4[0], p4[1], outline=color, fill="", width=2)

        if self.drag_mode == "marquee" and self.marquee_start and self.marquee_current:
            x0, y0 = self.marquee_start
            x1, y1 = self.marquee_current
            min_x, max_x = sorted((x0, x1))
            min_y, max_y = sorted((y0, y1))
            p1 = self._scene_to_canvas(float(min_x), float(min_y))
            p2 = self._scene_to_canvas(float(max_x), float(min_y))
            p3 = self._scene_to_canvas(float(max_x), float(max_y))
            p4 = self._scene_to_canvas(float(min_x), float(max_y))
            self.canvas.create_polygon(p1[0], p1[1], p2[0], p2[1], p3[0], p3[1], p4[0], p4[1], outline="#60a5fa", fill="", dash=(4, 3), width=2)

        bounds = self._selected_bounds()
        if bounds is not None and self.tool_var.get() == "select":
            x0, y0, x1, y1 = bounds
            p1 = self._scene_to_canvas(float(x0), float(y0))
            p2 = self._scene_to_canvas(float(x1), float(y0))
            p3 = self._scene_to_canvas(float(x1), float(y1))
            p4 = self._scene_to_canvas(float(x0), float(y1))
            self.canvas.create_polygon(p1[0], p1[1], p2[0], p2[1], p3[0], p3[1], p4[0], p4[1], outline="#5eead4", fill="", width=2, dash=(3, 2))
            hs = max(2, z)
            for _name, (hx, hy) in self._handle_positions(bounds).items():
                vx, vy = self._scene_to_canvas(float(hx), float(hy))
                self.canvas.create_rectangle(vx - hs, vy - hs, vx + hs, vy + hs, fill="#5eead4", outline="#083344")
            rx, ry = self._rotation_handle_pos(bounds)
            rvx, rvy = self._scene_to_canvas(float(rx), float(ry))
            self.canvas.create_line((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0, rvx, rvy, fill="#fb7185", width=1)
            self.canvas.create_oval(rvx - hs, rvy - hs, rvx + hs, rvy + hs, fill="#fb7185", outline="#7f1d1d")

        pvx, pvy = self._get_transform_pivot()
        plx, ply = self._scene_to_canvas(float(pvx - 2), float(pvy))
        prx, pry = self._scene_to_canvas(float(pvx + 2), float(pvy))
        ptx, pty = self._scene_to_canvas(float(pvx), float(pvy - 2))
        pbx, pby = self._scene_to_canvas(float(pvx), float(pvy + 2))
        self.canvas.create_line(plx, ply, prx, pry, fill="#f59e0b", width=2)
        self.canvas.create_line(ptx, pty, pbx, pby, fill="#f59e0b", width=2)

        if self.mirror_guide_axis in ("h", "v"):
            guide = "#f97316"
            if self.mirror_guide_axis == "h":
                gx0, gy0 = self._scene_to_canvas(float(pvx), 0.0)
                gx1, gy1 = self._scene_to_canvas(float(pvx), float(H))
            else:
                gx0, gy0 = self._scene_to_canvas(0.0, float(pvy))
                gx1, gy1 = self._scene_to_canvas(float(W), float(pvy))
            self.canvas.create_line(gx0, gy0, gx1, gy1, fill=guide, width=2, dash=(5, 3))

        self._refresh_layers()

    def _selected_rel_from_tree(self) -> str | None:
        sel = self.tree.selection()
        if not sel:
            return None
        return self.item_rel_by_iid.get(sel[0])

    def _on_tree_select(self) -> None:
        rel = self._selected_rel_from_tree()
        if not rel:
            self.current_rel = None
            self.preview_canvas.delete("all")
            return
        self.current_rel = rel
        self._update_sprite_preview(rel)

    def _update_sprite_preview(self, rel: str) -> None:
        self.preview_canvas.delete("all")
        img = self._resolve_image(rel)
        if img is None:
            return
        iw, ih = img.size
        if iw <= 0 or ih <= 0:
            return

        _cw, _ch, nw, nh, ox, oy = self._preview_metrics(iw, ih)
        view = img.resize((nw, nh), Image.Resampling.NEAREST)
        key = f"preview:{rel}:{nw}:{nh}"
        self.tk_cache[key] = ImageTk.PhotoImage(view)
        self.preview_canvas.create_image(ox, oy, image=self.tk_cache[key], anchor="nw")

        cell = max(1, int(self.cell_size_var.get()))
        self.sheet_cols = max(1, iw // cell)
        self.sheet_rows = max(1, ih // cell)

        if self.sheet_cols > 1 or self.sheet_rows > 1:
            px = nw / float(iw)
            py = nh / float(ih)
            for gx in range(0, iw + 1, cell):
                x = ox + int(gx * px)
                self.preview_canvas.create_line(x, oy, x, oy + nh, fill="#335")
            for gy in range(0, ih + 1, cell):
                y = oy + int(gy * py)
                self.preview_canvas.create_line(ox, y, ox + nw, y, fill="#335")

            cx, cy = self.sheet_selected
            cx = max(0, min(self.sheet_cols - 1, cx))
            cy = max(0, min(self.sheet_rows - 1, cy))
            self.sheet_selected = (cx, cy)
            sx = ox + int((cx * cell) * px)
            sy = oy + int((cy * cell) * py)
            ex = ox + int(((cx + 1) * cell) * px)
            ey = oy + int(((cy + 1) * cell) * py)
            self.preview_canvas.create_rectangle(sx, sy, ex, ey, outline="#00c8ff", width=2)

        self.preview_canvas.create_text(4, 4, text=rel.replace("/", " -> "), fill="#ddd", anchor="nw")

    def _on_preview_click(self, event) -> None:
        if not self.current_rel:
            return
        img = self._resolve_image(self.current_rel)
        if img is None:
            return
        iw, ih = img.size
        _cw, _ch, nw, nh, ox, oy = self._preview_metrics(iw, ih)

        if not (ox <= event.x < ox + nw and oy <= event.y < oy + nh):
            return

        px = int((event.x - ox) * iw / max(1, nw))
        py = int((event.y - oy) * ih / max(1, nh))
        cell = max(1, int(self.cell_size_var.get()))
        self.sheet_selected = (px // cell, py // cell)
        self._update_sprite_preview(self.current_rel)

    def _on_preview_drag(self, event) -> None:
        self._on_preview_click(event)

    def _build_sprite_item(self, rel: str, px: int, py: int) -> dict | None:
        img = self._resolve_image(rel)
        if img is None:
            return None
        iw, ih = img.size
        cell = max(1, int(self.cell_size_var.get()))

        sx = 0
        sy = 0
        sw = iw
        sh = ih
        if iw > cell or ih > cell:
            cx, cy = self.sheet_selected
            cols = max(1, iw // cell)
            rows = max(1, ih // cell)
            cx = max(0, min(cols - 1, cx))
            cy = max(0, min(rows - 1, cy))
            sx = cx * cell
            sy = cy * cell
            sw = min(cell, iw - sx)
            sh = min(cell, ih - sy)

        x, y = self._clamp_grid(px, py)
        return {
            "type": "sprite",
            "layer_id": self.active_layer_id,
            "path": rel,
            "x": x,
            "y": y,
            "w": max(1, sw),
            "h": max(1, sh),
            "src_x": sx,
            "src_y": sy,
            "src_w": sw,
            "src_h": sh,
            "rot": 0,
            "flip_x": False,
            "flip_y": False,
        }

    def _paint_at(self, x: int, y: int) -> None:
        rel = self._selected_rel_from_tree()
        if not rel:
            self.status_var.set("Select a sprite to paint")
            return
        item = self._build_sprite_item(rel, x, y)
        if item is None:
            return

        key = (
            item["path"],
            int(item["x"]),
            int(item["y"]),
            int(item["src_x"]),
            int(item["src_y"]),
            int(item["src_w"]),
            int(item["src_h"]),
        )
        if key == self.last_paint_key:
            return
        self.last_paint_key = key

        for i in range(len(self.items) - 1, -1, -1):
            it = self.items[i]
            self._ensure_item_layer(it)
            if str(it.get("layer_id", "base")) != self.active_layer_id:
                continue
            if it.get("type") != "sprite":
                continue
            if int(it.get("x", -9999)) == int(item["x"]) and int(it.get("y", -9999)) == int(item["y"]):
                self.items.pop(i)
                break

        self.items.append(item)
        self.selected_indices = {len(self.items) - 1}
        self.selected_index = len(self.items) - 1

    def _add_selected_sprite(self) -> None:
        rel = self._selected_rel_from_tree()
        if not rel:
            self.status_var.set("Select a sprite first")
            return
        item = self._build_sprite_item(rel, W // 2, H // 2)
        if item is None:
            self.status_var.set(f"Missing sprite: {rel}")
            return

        self._push_undo()
        item["x"], item["y"] = self._clamp_grid((W - int(item["w"])) // 2, (H - int(item["h"])) // 2)
        self.items.append(item)
        self.selected_indices = {len(self.items) - 1}
        self.selected_index = len(self.items) - 1
        self._update_prop_fields()
        self._render_canvas()
        self.status_var.set(f"Added {rel}")

    def _add_from_file(self) -> None:
        fp = filedialog.askopenfilename(title="Select PNG sprite", filetypes=[("PNG files", "*.png")], initialdir=str(ASSETS))
        if not fp:
            return
        p = Path(fp)
        try:
            rel = p.relative_to(ASSETS).as_posix()
        except ValueError:
            self.status_var.set("Sprite must be inside assets/")
            return

        if p not in self.sprites:
            self.sprites.append(p)
            self.sprites = sorted(self.sprites)
            self._refresh_tree()

        iid = self.iid_by_rel.get(rel)
        if iid:
            self.tree.selection_set(iid)
            self.tree.focus(iid)
            self.tree.see(iid)
            self.current_rel = rel
            self._update_sprite_preview(rel)
        self._add_selected_sprite()

    def _item_at(self, x: int, y: int) -> int | None:
        for i in range(len(self.items) - 1, -1, -1):
            it = self.items[i]
            self._ensure_item_layer(it)
            lid = str(it.get("layer_id", "base"))
            if not self._layer_is_visible(lid):
                continue
            ix, iy = int(it.get("x", 0)), int(it.get("y", 0))
            iw, ih = int(it.get("w", 1)), int(it.get("h", 1))
            if ix <= x < ix + max(1, iw) and iy <= y < iy + max(1, ih):
                return i
        return None

    def _create_tool_item(self, tool: str, x: int, y: int) -> dict:
        if tool == "line":
            return {
                "type": "line",
                "layer_id": self.active_layer_id,
                "x": x,
                "y": y,
                "x2": min(W - 1, x + 20),
                "y2": y,
                "w": 20,
                "h": 1,
                "color": self.shape_color_var.get().strip() or "#ffffff",
                "stroke": max(1, int(self.shape_width_var.get())),
            }
        if tool == "rect":
            return {
                "type": "rect",
                "layer_id": self.active_layer_id,
                "x": x,
                "y": y,
                "w": 24,
                "h": 14,
                "color": self.shape_color_var.get().strip() or "#ffffff",
                "stroke": max(1, int(self.shape_width_var.get())),
            }
        if tool == "text":
            return {
                "type": "text",
                "layer_id": self.active_layer_id,
                "x": x,
                "y": y,
                "w": 32,
                "h": 8,
                "text": self.text_value_var.get()[:64],
                "color": self.text_color_var.get().strip() or "#ffffff",
            }
        if tool == "char_marker":
            return {"type": "char_marker", "layer_id": self.active_layer_id, "x": x, "y": y, "w": 16, "h": 24}
        if tool == "enemy_marker":
            return {"type": "enemy_marker", "layer_id": self.active_layer_id, "x": x, "y": y, "w": 24, "h": 24}
        return {}

    def _on_click(self, event) -> None:
        px, py = self._event_to_scene(event)
        tool = self.tool_var.get()
        shift = bool(event.state & 0x0001)

        if tool == "select":
            if self._hit_rotation_handle(px, py) and self.selected_indices:
                self._push_undo()
                self.drag_mode = "rotate"
                self.rotate_pivot = self._get_transform_pivot()
                pvx, pvy = self.rotate_pivot
                self.rotate_start_angle = math.degrees(math.atan2(py - pvy, px - pvx))
                self.rotate_start_items = {
                    i: json.loads(json.dumps(self.items[i])) for i in self.selected_indices if 0 <= i < len(self.items)
                }
                return

            handle = self._hit_transform_handle(px, py)
            if handle and self.selected_indices:
                bounds = self._selected_bounds()
                if bounds is not None:
                    self._push_undo()
                    self.drag_mode = "scale"
                    self.scale_handle = handle
                    self.scale_start_items = {
                        i: json.loads(json.dumps(self.items[i])) for i in self.selected_indices if 0 <= i < len(self.items)
                    }
                    pos = self._handle_positions(bounds)
                    self.scale_start_handle_pos = pos[handle]
                    opp = self._opposite_handle(handle)
                    self.scale_pivot = pos[opp]
                    return

            idx = self._item_at(px, py)
            if idx is not None:
                hit_layer = str(self.items[idx].get("layer_id", "base"))
                if self._layer_is_locked(hit_layer):
                    self.status_var.set("Layer is locked")
                    return
                if shift:
                    if idx in self.selected_indices:
                        self.selected_indices.remove(idx)
                        if self.selected_index == idx:
                            self.selected_index = next(iter(self.selected_indices), None)
                    else:
                        self.selected_indices.add(idx)
                        self.selected_index = idx
                else:
                    if idx not in self.selected_indices:
                        self.selected_indices = {idx}
                    self.selected_index = idx

                self.drag_mode = "move"
                self.drag_start = (px, py)
                self.drag_start_positions = {
                    i: (int(self.items[i].get("x", 0)), int(self.items[i].get("y", 0))) for i in self.selected_indices
                }
                self._push_undo()
            else:
                if not shift:
                    self.selected_indices.clear()
                    self.selected_index = None
                self.drag_mode = "marquee"
                self.marquee_start = (px, py)
                self.marquee_current = (px, py)
            self._update_prop_fields()
            self._render_canvas()
            return

        if tool == "paint":
            if self._layer_is_locked(self.active_layer_id):
                self.status_var.set("Active layer is locked")
                return
            self._push_undo()
            self.drag_mode = "paint"
            self.last_paint_key = None
            if self.tilemap_mode_var.get():
                self._apply_tile_brush(px, py)
            else:
                self._paint_at(px, py)
            self._update_prop_fields()
            self._render_canvas()
            return

        self._push_undo()
        item = self._create_tool_item(tool, *self._clamp_grid(px, py))
        if not item:
            return
        if self._layer_is_locked(self.active_layer_id):
            self.status_var.set("Active layer is locked")
            return
        self.items.append(item)
        self.selected_indices = {len(self.items) - 1}
        self.selected_index = len(self.items) - 1
        self.drag_mode = "draw"
        self.drag_start = (int(item.get("x", px)), int(item.get("y", py)))
        self._update_prop_fields()
        self._render_canvas()

    def _on_drag(self, event) -> None:
        px, py = self._event_to_scene(event)
        if self.snap_var.get():
            px, py = self._clamp_grid(px, py)

        if self.drag_mode == "rotate":
            self._rotate_selected_drag(px, py)
            return

        if self.drag_mode == "scale":
            self._scale_selected_with_handle(px, py)
            return

        if self.drag_mode == "paint":
            if self.tilemap_mode_var.get():
                self._apply_tile_brush(px, py)
            else:
                self._paint_at(px, py)
            self._render_canvas()
            return

        if self.drag_mode == "marquee":
            self.marquee_current = (px, py)
            self._render_canvas()
            return

        if self.drag_mode == "draw":
            if self.selected_index is None:
                return
            it = self.items[self.selected_index]
            t = it.get("type", "sprite")
            if t in ("line", "rect", "char_marker", "enemy_marker"):
                x0, y0 = int(it.get("x", 0)), int(it.get("y", 0))
                it["w"] = max(1, px - x0)
                it["h"] = max(1, py - y0)
                if t == "line":
                    it["x2"] = x0 + it["w"]
                    it["y2"] = y0 + it["h"]
                self._update_prop_fields()
                self._render_canvas()
            return

        if self.drag_mode == "move":
            if not self.selected_indices or self.selected_index is None:
                return
            sx, sy = self.drag_start
            dx = px - sx
            dy = py - sy
            for i in self.selected_indices:
                x0, y0 = self.drag_start_positions.get(i, (int(self.items[i].get("x", 0)), int(self.items[i].get("y", 0))))
                it = self.items[i]
                self._ensure_item_layer(it)
                if self._layer_is_locked(str(it.get("layer_id", "base"))):
                    continue
                w = max(1, int(it.get("w", 1)))
                h = max(1, int(it.get("h", 1)))
                nx = max(0, min(W - w, x0 + dx))
                ny = max(0, min(H - h, y0 + dy))
                if self.snap_var.get():
                    nx, ny = self._clamp_grid(nx, ny)
                it["x"] = nx
                it["y"] = ny
                if it.get("type") == "line":
                    it["x2"] = nx + int(it.get("w", 1))
                    it["y2"] = ny + int(it.get("h", 1))
            self._update_prop_fields()
            self._render_canvas()

    def _on_release(self, event) -> None:
        if self.drag_mode == "marquee" and self.marquee_start is not None:
            x0, y0 = self.marquee_start
            x1, y1 = self._event_to_scene(event)
            min_x, max_x = sorted((x0, x1))
            min_y, max_y = sorted((y0, y1))

            selected: set[int] = set()
            for i, it in enumerate(self.items):
                ix = int(it.get("x", 0))
                iy = int(it.get("y", 0))
                iw = int(it.get("w", 1))
                ih = int(it.get("h", 1))
                if ix < max_x and ix + iw > min_x and iy < max_y and iy + ih > min_y:
                    selected.add(i)

            if bool(event.state & 0x0001):
                self.selected_indices |= selected
            else:
                self.selected_indices = selected
            self.selected_index = max(self.selected_indices) if self.selected_indices else None
            self._update_prop_fields()

        self.drag_mode = None
        self.marquee_start = None
        self.marquee_current = None
        self.scale_handle = None
        self.scale_start_items.clear()
        self.rotate_start_items.clear()
        self.last_paint_key = None
        self._render_canvas()

    def _on_right_click(self, event) -> None:
        if self.tool_var.get() != "paint" or not self.tilemap_mode_var.get():
            return
        px, py = self._event_to_scene(event)
        if self.snap_var.get():
            px, py = self._clamp_grid(px, py)
        self._tile_flood_fill(px, py)

    def _update_prop_fields(self) -> None:
        if self.selected_index is None or self.selected_index >= len(self.items):
            return
        it = self.items[self.selected_index]
        self.prop_vars["x"].set(int(it.get("x", 0)))
        self.prop_vars["y"].set(int(it.get("y", 0)))
        self.prop_vars["w"].set(int(it.get("w", 8)))
        self.prop_vars["h"].set(int(it.get("h", 8)))
        self.prop_vars["src_x"].set(int(it.get("src_x", 0)))
        self.prop_vars["src_y"].set(int(it.get("src_y", 0)))
        self.prop_vars["src_w"].set(int(it.get("src_w", int(it.get("w", 8)))))
        self.prop_vars["src_h"].set(int(it.get("src_h", int(it.get("h", 8)))))

    def _apply_props(self) -> None:
        if self.selected_index is None:
            self.status_var.set("No selection")
            return

        self._push_undo()
        targets = sorted(self.selected_indices) if self.selected_indices else [self.selected_index]
        for i in targets:
            if i < 0 or i >= len(self.items):
                continue
            it = self.items[i]
            it["x"], it["y"] = self._clamp_grid(int(self.prop_vars["x"].get()), int(self.prop_vars["y"].get()))
            it["w"] = max(1, int(self.prop_vars["w"].get()))
            it["h"] = max(1, int(self.prop_vars["h"].get()))

            if it.get("type") == "sprite":
                rel = it.get("path", "")
                img = self._resolve_image(rel)
                iw, ih = (img.size if img is not None else (it["w"], it["h"]))
                sx = max(0, int(self.prop_vars["src_x"].get()))
                sy = max(0, int(self.prop_vars["src_y"].get()))
                sw = max(1, int(self.prop_vars["src_w"].get()))
                sh = max(1, int(self.prop_vars["src_h"].get()))
                if sx + sw > iw:
                    sw = max(1, iw - sx)
                if sy + sh > ih:
                    sh = max(1, ih - sy)
                it["src_x"] = sx
                it["src_y"] = sy
                it["src_w"] = sw
                it["src_h"] = sh

            if it.get("type") == "line":
                it["x2"] = int(it["x"]) + int(it["w"])
                it["y2"] = int(it["y"]) + int(it["h"])

        self._render_canvas()

    def _load_scene(self) -> None:
        f = self._scene_file()
        if not f.exists():
            self.items = []
            self.selected_indices.clear()
            self.selected_index = None
            self._render_canvas()
            self._set_place_seed_for_current_scene()
            self.status_var.set(f"No layout yet for {self.scene_var.get()}")
            return

        payload = json.loads(f.read_text(encoding="utf-8"))
        defs = payload.get("layer_defs", [{"id": "base", "name": "Base", "visible": True, "locked": False}])
        if not isinstance(defs, list) or not defs:
            defs = [{"id": "base", "name": "Base", "visible": True, "locked": False}]
        has_base = any(str(d.get("id", "")) == "base" for d in defs if isinstance(d, dict))
        if not has_base:
            defs = [{"id": "base", "name": "Base", "visible": True, "locked": False}] + defs
        self.layer_defs = [d for d in defs if isinstance(d, dict)]
        self.active_layer_id = str(payload.get("active_layer_id", "base"))
        if self.active_layer_id not in self._layer_def_map():
            self.active_layer_id = "base"

        self.items = payload.get("items", [])
        grid_cell = int(payload.get("grid_cell", self.cell_size_var.get()))
        self.cell_size_var.set(max(1, grid_cell))
        self.selected_indices.clear()
        self.selected_index = None
        self.undo_stack.clear()
        self.redo_stack.clear()
        self._render_canvas()
        self._set_place_seed_for_current_scene()
        self.status_var.set(f"Loaded {f.name}")

    def _save_scene(self) -> None:
        LAYOUTS.mkdir(parents=True, exist_ok=True)
        payload = self._scene_payload()
        f = self._scene_file()
        f.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        seed = self._build_scene_seed(payload)
        self.scene_seed_db[self.scene_var.get()] = seed
        self._save_scene_seed_db()
        self._upsert_library_entry(
            {
                "seed_code": seed,
                "kind": "place",
                "title": "Place " + self.scene_var.get(),
                "tags": ["place", self.scene_var.get()],
                "meta": {
                    "scene": self.scene_var.get(),
                    "dependencies": self._extract_place_dependencies(seed),
                },
            }
        )
        self.place_seed_var.set(seed)
        self.place_seed_info_var.set("Saved and seeded scene " + self.scene_var.get())
        self.status_var.set(f"Saved {f}")

    def _draw_item_on_image(self, canvas: Image.Image, item: dict) -> None:
        from PIL import ImageDraw, ImageFont

        draw = ImageDraw.Draw(canvas)
        font = ImageFont.load_default()

        t = item.get("type", "sprite")
        x = int(item.get("x", 0))
        y = int(item.get("y", 0))
        w = int(item.get("w", 8))
        h = int(item.get("h", 8))

        if t == "sprite":
            rel = item.get("path", "")
            img = self._resolve_image(rel)
            if img is None:
                return
            sx = int(item.get("src_x", 0))
            sy = int(item.get("src_y", 0))
            sw = int(item.get("src_w", img.size[0]))
            sh = int(item.get("src_h", img.size[1]))
            crop = img.crop((sx, sy, sx + sw, sy + sh))
            if bool(item.get("flip_x", False)):
                crop = crop.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            if bool(item.get("flip_y", False)):
                crop = crop.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            rot = int(item.get("rot", 0)) % 360
            if rot:
                crop = crop.rotate(-rot, expand=True, resample=Image.Resampling.NEAREST)
            sprite = crop.resize((max(1, w), max(1, h)), Image.Resampling.NEAREST)
            canvas.alpha_composite(sprite, (x, y))
            return

        if t == "text":
            draw.text((x, y), item.get("text", "Text"), fill=item.get("color", "#ffffff"), font=font)
            return

        if t == "line":
            x2 = int(item.get("x2", x + w))
            y2 = int(item.get("y2", y + h))
            draw.line((x, y, x2, y2), fill=item.get("color", "#ffffff"), width=max(1, int(item.get("stroke", 1))))
            return

        if t == "rect":
            draw.rectangle((x, y, x + w, y + h), outline=item.get("color", "#ffffff"), width=max(1, int(item.get("stroke", 1))))
            return

        if t == "char_marker":
            draw.rectangle((x, y, x + w, y + h), outline="#22cc22", width=1)
            return

        if t == "enemy_marker":
            draw.rectangle((x, y, x + w, y + h), outline="#ff3333", width=1)

    def _export_bmp(self) -> None:
        canvas = Image.new("RGBA", (W, H), (10, 12, 16, 255))
        for it in self.items:
            self._draw_item_on_image(canvas, it)

        out_name = SCENE_NAMES.get(self.scene_var.get(), self.scene_var.get() + ".bmp")
        RUNTIME_BG.mkdir(parents=True, exist_ok=True)
        out = RUNTIME_BG / out_name
        canvas.convert("RGB").save(out, format="BMP")
        self.status_var.set(f"Exported {out}")

    def _clear_scene(self) -> None:
        if self.items:
            self._push_undo()
        self.items = []
        self.selected_indices.clear()
        self.selected_index = None
        self._render_canvas()
        self.status_var.set("Cleared scene")

    def _copy_selected(self) -> None:
        if not self.selected_indices:
            self.status_var.set("No selected item")
            return
        self.clipboard_items = [json.loads(json.dumps(self.items[i])) for i in sorted(self.selected_indices)]
        self.status_var.set(f"Copied {len(self.clipboard_items)} item(s)")

    def _paste_clipboard(self) -> None:
        if not self.clipboard_items:
            self.status_var.set("Clipboard empty")
            return
        self._push_undo()
        new_sel: set[int] = set()
        for cp0 in self.clipboard_items:
            cp = json.loads(json.dumps(cp0))
            cp["x"], cp["y"] = self._clamp_grid(int(cp.get("x", 0)) + 3, int(cp.get("y", 0)) + 3)
            self.items.append(cp)
            new_sel.add(len(self.items) - 1)
        self.selected_indices = new_sel
        self.selected_index = max(new_sel) if new_sel else None
        self._update_prop_fields()
        self._render_canvas()
        self.status_var.set(f"Pasted {len(new_sel)} item(s)")

    def _duplicate_selected(self) -> None:
        if not self.selected_indices:
            self.status_var.set("No selected item")
            return
        self._copy_selected()
        self._paste_clipboard()

    def _replace_selected_sprite(self) -> None:
        if not self.selected_indices:
            self.status_var.set("No selected item")
            return
        rel = self._selected_rel_from_tree()
        if not rel:
            self.status_var.set("Select a sprite in browser to replace")
            return

        img = self._resolve_image(rel)
        if img is None:
            self.status_var.set("Missing sprite")
            return

        self._push_undo()
        count = 0
        for i in self.selected_indices:
            it = self.items[i]
            if it.get("type") != "sprite":
                continue
            it["path"] = rel
            it["src_x"] = 0
            it["src_y"] = 0
            it["src_w"] = max(1, int(it.get("src_w", img.size[0])))
            it["src_h"] = max(1, int(it.get("src_h", img.size[1])))
            it["w"] = max(1, min(W, int(it.get("w", it["src_w"]))))
            it["h"] = max(1, min(H, int(it.get("h", it["src_h"]))))
            count += 1

        self._update_prop_fields()
        self._render_canvas()
        self.status_var.set(f"Replaced {count} sprite(s)")

    def _delete_selected_item(self) -> None:
        if not self.selected_indices:
            self.status_var.set("No selected item")
            return
        self._push_undo()
        for i in sorted(self.selected_indices, reverse=True):
            if 0 <= i < len(self.items):
                self.items.pop(i)
        self.selected_indices.clear()
        self.selected_index = None
        self._render_canvas()
        self.status_var.set("Deleted")

    def _nudge(self, dx: int, dy: int) -> None:
        if not self.selected_indices:
            return
        self._push_undo()
        step = max(1, int(self.cell_size_var.get())) if self.snap_var.get() else 1
        for i in sorted(self.selected_indices):
            it = self.items[i]
            w = int(it.get("w", 1))
            h = int(it.get("h", 1))
            nx = max(0, min(W - w, int(it.get("x", 0)) + dx * step))
            ny = max(0, min(H - h, int(it.get("y", 0)) + dy * step))
            if self.snap_var.get():
                nx, ny = self._clamp_grid(nx, ny)
            it["x"] = nx
            it["y"] = ny
            if it.get("type") == "line":
                it["x2"] = nx + int(it.get("w", 1))
                it["y2"] = ny + int(it.get("h", 1))
        self._update_prop_fields()
        self._render_canvas()

    def _layer_up(self) -> None:
        if not self.selected_indices:
            return
        self._push_undo()
        for i in sorted(self.selected_indices):
            if i <= 0:
                continue
            self.items[i - 1], self.items[i] = self.items[i], self.items[i - 1]
        self.selected_indices = {max(0, i - 1) for i in self.selected_indices}
        self.selected_index = max(self.selected_indices) if self.selected_indices else None
        self._render_canvas()

    def _layer_down(self) -> None:
        if not self.selected_indices:
            return
        self._push_undo()
        for i in sorted(self.selected_indices, reverse=True):
            if i >= len(self.items) - 1:
                continue
            self.items[i + 1], self.items[i] = self.items[i], self.items[i + 1]
        self.selected_indices = {min(len(self.items) - 1, i + 1) for i in self.selected_indices}
        self.selected_index = max(self.selected_indices) if self.selected_indices else None
        self._render_canvas()

    def _layer_top(self) -> None:
        if not self.selected_indices:
            return
        self._push_undo()
        selected = [self.items[i] for i in sorted(self.selected_indices)]
        remain = [self.items[i] for i in range(len(self.items)) if i not in self.selected_indices]
        self.items = remain + selected
        base = len(remain)
        self.selected_indices = set(range(base, len(self.items)))
        self.selected_index = max(self.selected_indices)
        self._render_canvas()

    def _layer_bottom(self) -> None:
        if not self.selected_indices:
            return
        self._push_undo()
        selected = [self.items[i] for i in sorted(self.selected_indices)]
        remain = [self.items[i] for i in range(len(self.items)) if i not in self.selected_indices]
        self.items = selected + remain
        self.selected_indices = set(range(0, len(selected)))
        self.selected_index = max(self.selected_indices) if self.selected_indices else None
        self._render_canvas()

    def _on_layer_select(self) -> None:
        sel = {int(i) for i in self.layers_list.curselection()}
        self.selected_indices = {i for i in sel if 0 <= i < len(self.items)}
        self.selected_index = max(self.selected_indices) if self.selected_indices else None
        self._update_prop_fields()
        self._render_canvas()


def main() -> None:
    root = tk.Tk()
    Builder(root)
    root.mainloop()


if __name__ == "__main__":
    main()
