"""Integrity manifest helpers with sha256 hashing."""

try:
    import hashlib
except Exception:  # MicroPython fallback name.
    import uhashlib as hashlib  # type: ignore

import json
import os

from kernel_core import PATHS
from storage import get_data_root, load_json, save_json


def _sha256_bytes(data):
    hasher = hashlib.sha256()
    hasher.update(data)
    return hasher.hexdigest()


def file_sha256(path):
    try:
        with open(path, "rb") as handle:
            return _sha256_bytes(handle.read())
    except Exception:
        return None


def build_manifest(rel_paths):
    root = get_data_root()
    manifest = {}
    for rel_path in rel_paths:
        full = root + "/" + rel_path
        digest = file_sha256(full)
        if digest:
            manifest[rel_path] = digest
    save_json(PATHS["manifest"], manifest)
    return manifest


def verify_manifest(rel_path):
    root = get_data_root()
    manifest = load_json(PATHS["manifest"], {})
    if rel_path not in manifest:
        return True, "no-manifest-entry"

    full = root + "/" + rel_path
    current = file_sha256(full)
    if not current:
        return False, "missing-file"
    if current != manifest[rel_path]:
        return False, "hash-mismatch"
    return True, "ok"


def validate_json_file(rel_path):
    root = get_data_root()
    full = root + "/" + rel_path
    ok, reason = verify_manifest(rel_path)
    if not ok:
        return False, reason

    try:
        with open(full, "r") as handle:
            json.load(handle)
        return True, "ok"
    except Exception:
        return False, "invalid-json"
