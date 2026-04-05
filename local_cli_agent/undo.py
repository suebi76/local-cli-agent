# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Steffen Schwabe
"""
undo.py — Session-level undo stack for file operations.

Before every write_file or edit_file, executor.py calls save_checkpoint()
with the current file content. /undo restores the last N snapshots.
The stack lives in memory — it resets when the process restarts.
"""
import os
from datetime import datetime

# ── Undo stack ────────────────────────────────────────────────────────────────
_stack: list[dict] = []
_MAX = 30  # max checkpoints kept in memory


def save_checkpoint(label: str, paths: list[str]) -> None:
    """
    Snapshot the current content of the given files.
    Call this BEFORE any write — it records the state to restore on undo.

    paths: list of absolute file paths about to be modified/created.
           Files that don't exist yet are recorded as non-existent so undo
           can delete them.
    """
    files = []
    for path in paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                files.append({"path": path, "content": content, "existed": True})
            except Exception:
                files.append({"path": path, "content": None, "existed": True})
        else:
            files.append({"path": path, "content": None, "existed": False})

    _stack.append({
        "label": label,
        "files": files,
        "ts": datetime.now().strftime("%H:%M:%S"),
    })
    if len(_stack) > _MAX:
        _stack.pop(0)


def save_manual_checkpoint(label: str = "manuell") -> str:
    """Save an empty marker checkpoint (no file snapshots)."""
    _stack.append({
        "label": f"[checkpoint] {label}",
        "files": [],
        "ts": datetime.now().strftime("%H:%M:%S"),
    })
    if len(_stack) > _MAX:
        _stack.pop(0)
    return f"Checkpoint gesetzt: '{label}'"


def undo(n: int = 1) -> str:
    """
    Undo the last n operations by restoring file snapshots.
    Returns a human-readable summary.
    """
    if not _stack:
        return "Nichts zum Rückgängigmachen — Undo-Verlauf ist leer."

    n = min(n, len(_stack))
    restored, deleted, skipped, errors = [], [], [], []

    for _ in range(n):
        checkpoint = _stack.pop()
        for fs in checkpoint["files"]:
            path = fs["path"]
            try:
                if not fs["existed"]:
                    # File was created by the agent — delete it on undo
                    if os.path.exists(path):
                        os.remove(path)
                        deleted.append(os.path.basename(path))
                    else:
                        skipped.append(os.path.basename(path))
                elif fs["content"] is not None:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(fs["content"])
                    restored.append(os.path.basename(path))
                else:
                    skipped.append(os.path.basename(path))
            except Exception as e:
                errors.append(f"{os.path.basename(path)}: {e}")

    lines = [f"Undo ({n} Aktion{'en' if n > 1 else ''}):"]
    for r in restored:
        lines.append(f"  ✓ Wiederhergestellt: {r}")
    for d in deleted:
        lines.append(f"  ✓ Gelöscht (war neu): {d}")
    for s in skipped:
        lines.append(f"  – Übersprungen (kein Snapshot): {s}")
    for e in errors:
        lines.append(f"  ✗ Fehler: {e}")
    if not restored and not deleted and not skipped and not errors:
        lines.append("  (keine Dateioperationen in diesem Checkpoint)")
    return "\n".join(lines)


def history() -> str:
    """Return a formatted undo history."""
    if not _stack:
        return "Undo-Verlauf ist leer."
    lines = [f"Undo-Verlauf ({len(_stack)} Einträge, älteste zuerst):"]
    for i, cp in enumerate(_stack, 1):
        n_files = len(cp["files"])
        lines.append(f"  [{i:2}] {cp['ts']}  {cp['label']}  ({n_files} Datei{'en' if n_files != 1 else ''})")
    lines.append("\nMit /undo [n] die letzten n Aktionen rückgängig machen.")
    return "\n".join(lines)


def size() -> int:
    return len(_stack)
