# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Steffen Schwabe
"""
Persistent user settings — saved to <data_dir>/settings.json

Currently persisted:
  active_profile  — last used agent profile (e.g. "vibe", "debugger")
  autotest_cmd    — auto-test command or null (e.g. "pytest tests/")
  max_tokens      — max output tokens (e.g. 4096)
"""

import json
import os

from local_cli_agent.constants import SCRIPT_DIR

_SETTINGS_FILE = os.path.join(SCRIPT_DIR, "settings.json")

_DEFAULTS: dict = {
    "active_profile": "standard",
    "autotest_cmd": None,
    "max_tokens": 4096,
}


def load() -> dict:
    """Load all settings from disk. Missing keys fall back to defaults."""
    settings = dict(_DEFAULTS)
    if os.path.exists(_SETTINGS_FILE):
        try:
            with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Only keep keys we know about; ignore stale/unknown keys
            settings.update({k: v for k, v in data.items() if k in _DEFAULTS})
        except Exception:
            pass  # corrupted file → silently use defaults
    return settings


def save(settings: dict) -> None:
    """Persist the full settings dict to disk."""
    try:
        with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
    except Exception:
        pass  # never crash if settings can't be written


def get(key: str):
    """Return a single setting value."""
    return load().get(key, _DEFAULTS.get(key))


def set_value(key: str, value) -> None:
    """Update and persist a single setting."""
    if key not in _DEFAULTS:
        return
    settings = load()
    settings[key] = value
    save(settings)
