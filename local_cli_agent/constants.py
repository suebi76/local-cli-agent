# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Steffen Schwabe
import os
import site

# ── ANSI Colors ──────────────────────────────────────────────────────────────
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
RED = "\033[31m"
BLUE = "\033[34m"
WHITE = "\033[37m"

# ── Paths ─────────────────────────────────────────────────────────────────────
def _data_dir() -> str:
    """
    Return the directory used for user data (.env, memory, changelog).
    - Editable install (development): project root (one level above this file)
    - Global install (pip install):   ~/.local-cli-agent/
    """
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(pkg_dir)
    # If we're inside any site-packages directory it's a global install
    try:
        sp_dirs = site.getsitepackages()
    except AttributeError:
        sp_dirs = []
    if any(pkg_dir.startswith(sp) for sp in sp_dirs):
        d = os.path.join(os.path.expanduser("~"), ".local-cli-agent")
        os.makedirs(d, exist_ok=True)
        return d
    return project_root


SCRIPT_DIR  = _data_dir()
# For self_improve: always the real package source file
SCRIPT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cli.py")
ENV_FILE    = os.path.join(SCRIPT_DIR, ".env")
MEMORY_FILE = os.path.join(SCRIPT_DIR, ".local-cli-memory.json")
CHANGELOG   = os.path.join(SCRIPT_DIR, ".local-cli-changelog.json")
VERSION = "2.1.0"