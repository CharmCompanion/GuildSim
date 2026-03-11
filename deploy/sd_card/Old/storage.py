import json
import os

from sd_setup import mount_sd


DATA_ROOT = None


def get_data_root():
    global DATA_ROOT
    if DATA_ROOT:
        return DATA_ROOT

    base = mount_sd()
    if base:
        root = base
    else:
        root = "data"

    if root not in os.listdir(".") and root == "data":
        os.mkdir(root)

    DATA_ROOT = root
    return DATA_ROOT


def ensure_dir(path):
    parts = path.replace("\\", "/").split("/")
    current = ""
    for part in parts:
        if not part:
            continue
        current = part if not current else current + "/" + part
        try:
            os.mkdir(current)
        except OSError:
            pass


def load_json(rel_path, default_value):
    root = get_data_root()
    full_path = root + "/" + rel_path
    try:
        with open(full_path, "r") as handle:
            return json.load(handle)
    except Exception:
        return default_value


def save_json(rel_path, data):
    root = get_data_root()
    full_path = root + "/" + rel_path
    dir_path = "/".join(full_path.split("/")[:-1])
    if dir_path:
        ensure_dir(dir_path)
    with open(full_path, "w") as handle:
        json.dump(data, handle)
