# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Steffen Schwabe
import os
import json

from local_cli_agent.constants import MEMORY_FILE, SCRIPT_DIR

_LEGACY_MEMORY = os.path.join(SCRIPT_DIR, ".kimi-memory.json")


# ── Memory ──────────────────────────────────────────────────────────────────
def load_memory():
    """Load memory from file. Migrates legacy .kimi-memory.json if needed."""
    if not os.path.exists(MEMORY_FILE) and os.path.exists(_LEGACY_MEMORY):
        try:
            os.rename(_LEGACY_MEMORY, MEMORY_FILE)
        except OSError:
            pass
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_memory_file(data):
    """Save memory to file."""
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)