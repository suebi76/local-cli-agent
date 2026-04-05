# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Steffen Schwabe
"""
api.py – thin dispatcher to the active backend (Ollama / LM Studio).

The active model entry is set once at startup via set_entry().
All agent calls go through call_api() which forwards to backends.call_api().
"""
from local_cli_agent import backends as _backends

_active_entry = None   # active ModelEntry
_model_name = ""       # display name


def set_entry(entry) -> None:
    """Set the active model entry. Called once at startup."""
    global _active_entry, _model_name
    _active_entry = entry
    _model_name = entry.name if entry else ""


def get_model_name() -> str:
    return _model_name


def call_api(messages, thinking=True, temperature=None, max_tokens=4096, use_tools=True):
    """Dispatch to backends.call_api(). Returns (content, tool_calls)."""
    # 'thinking' and 'temperature' are accepted for API compatibility
    return _backends.call_api(_active_entry, messages, max_tokens=max_tokens, use_tools=use_tools)