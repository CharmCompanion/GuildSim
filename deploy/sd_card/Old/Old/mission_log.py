"""Mission log writer/reader using line-by-line text for low memory."""

import time

from kernel_core import PATHS
from storage import ensure_dir, get_data_root


def _log_dir():
    root = get_data_root()
    path = root + "/" + PATHS["guild_sim"] + "/logs"
    ensure_dir(path)
    return path


def _default_log_name():
    return "mission_{}.txt".format(int(time.time()))


def append_log_line(line, log_name=None):
    log_name = log_name or _default_log_name()
    path = _log_dir() + "/" + log_name
    with open(path, "a") as handle:
        handle.write(str(line) + "\n")
    return log_name


def read_log_chunks(log_name, chunk_size=256):
    path = _log_dir() + "/" + log_name
    with open(path, "r") as handle:
        while True:
            data = handle.read(chunk_size)
            if not data:
                break
            yield data


def tail_log(log_name, max_lines=20):
    path = _log_dir() + "/" + log_name
    lines = []
    with open(path, "r") as handle:
        for line in handle:
            lines.append(line.rstrip("\n"))
            if len(lines) > max_lines:
                lines.pop(0)
    return lines
