# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Steffen Schwabe
"""
Rich-based Markdown rendering for agent responses.
Falls back to plain print() if rich is not installed.
"""

try:
    from rich.console import Console
    from rich.markdown import Markdown
    _console = Console()
    _available = True
except ImportError:
    _available = False


def is_available() -> bool:
    """Return True if the rich library is installed."""
    return _available


def render(text: str) -> None:
    """Render text as Markdown with rich. Falls back to plain print."""
    if not text:
        return
    if not _available:
        print(text)
        return
    try:
        _console.print(Markdown(text))
    except Exception:
        # Safety net: if rich fails for any reason, fall back
        print(text)
