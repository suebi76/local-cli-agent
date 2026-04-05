# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Steffen Schwabe
"""
_env.py – loads .env file into os.environ BEFORE constants.py is imported.
This ensures LOCAL_CLI_OLLAMA_URL, LOCAL_CLI_LMSTUDIO_URL, and
LOCAL_CLI_LAST_MODEL are available at import time.
"""
import os


def load_env_early() -> None:
    """Read ~/.local-cli-agent/.env and project-root .env into os.environ."""
    candidates = [
        os.path.join(os.path.expanduser("~"), ".local-cli-agent", ".env"),
        # Also check next to the package for editable/dev installs
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
    ]
    for env_file in candidates:
        if not os.path.isfile(env_file):
            continue
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                # Only set if not already overridden by the real environment
                if key and key not in os.environ:
                    os.environ[key] = val