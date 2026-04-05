# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Steffen Schwabe
"""
watcher.py — File-system watch mode for Local CLI Agent.

Polls a path every N seconds. When files change, the agent is called
automatically with the user-defined instruction + a description of
what changed.

No extra dependencies — uses os.stat() polling.
"""
import os
import threading
import time

from local_cli_agent.constants import RESET, BOLD, DIM, CYAN, YELLOW, GREEN, RED

# ── Active watcher state (one watcher at a time) ─────────────────────────────
_stop_event: threading.Event | None = None
_watch_thread: threading.Thread | None = None


def _snapshot(path: str) -> dict[str, float]:
    """Return {abs_path: mtime} for all files under path."""
    snap: dict[str, float] = {}
    abs_path = os.path.abspath(path)
    skip = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}

    if os.path.isfile(abs_path):
        try:
            snap[abs_path] = os.path.getmtime(abs_path)
        except OSError:
            pass
        return snap

    if os.path.isdir(abs_path):
        for root, dirs, files in os.walk(abs_path):
            dirs[:] = [d for d in dirs if d not in skip and not d.startswith(".")]
            for f in files:
                fp = os.path.join(root, f)
                try:
                    snap[fp] = os.path.getmtime(fp)
                except OSError:
                    pass
    return snap


def _diff_snapshots(
    old: dict[str, float],
    new: dict[str, float],
    base: str,
) -> list[str]:
    """Return list of relative paths that were added or modified."""
    changed = []
    for path, mtime in new.items():
        if path not in old or old[path] != mtime:
            changed.append(os.path.relpath(path, base))
    return changed


def _watch_loop(
    path: str,
    instruction: str,
    agent_callback,        # callable(messages: list) -> None
    thinking: bool,
    max_tokens: int,
    interval: float,
    stop_event: threading.Event,
) -> None:
    from local_cli_agent.config import build_system_prompt

    abs_path = os.path.abspath(path)
    state = _snapshot(abs_path)
    consecutive_errors = 0

    while not stop_event.is_set():
        time.sleep(interval)
        if stop_event.is_set():
            break

        try:
            new_state = _snapshot(abs_path)
            changed = _diff_snapshots(state, new_state, abs_path)

            if changed:
                state = new_state
                consecutive_errors = 0
                label = ", ".join(changed[:5])
                if len(changed) > 5:
                    label += f" (+{len(changed) - 5} weitere)"

                print(f"\n{BOLD}{YELLOW}[watch]{RESET} Änderung erkannt: {CYAN}{label}{RESET}")

                user_msg = (
                    f"Geänderte Datei(en): {label}\n\n"
                    f"Anweisung: {instruction}"
                )
                messages = [
                    {"role": "system", "content": build_system_prompt()},
                    {"role": "user", "content": user_msg},
                ]
                try:
                    agent_callback(messages, thinking=thinking, max_tokens=max_tokens)
                except Exception as e:
                    print(f"\n{RED}[watch] Agent-Fehler: {e}{RESET}")
                print(f"\n{DIM}[watch] Warte auf weitere Änderungen... (Ctrl+C oder /watch stop){RESET}")
            else:
                state = new_state

        except Exception as e:
            consecutive_errors += 1
            if consecutive_errors <= 3:
                print(f"\n{RED}[watch] Fehler beim Prüfen von {path}: {e}{RESET}")
            if consecutive_errors > 10:
                print(f"\n{RED}[watch] Zu viele Fehler — Watch-Mode wird beendet.{RESET}")
                break


def start(
    path: str,
    instruction: str,
    agent_callback,
    thinking: bool = True,
    max_tokens: int = 4096,
    interval: float = 2.0,
) -> str:
    """Start the watcher in a background thread. Returns status message."""
    global _stop_event, _watch_thread

    if _watch_thread and _watch_thread.is_alive():
        return f"{YELLOW}Watch läuft bereits. Mit /watch stop beenden.{RESET}"

    abs_path = os.path.abspath(path)
    if not os.path.exists(abs_path):
        return f"{RED}Pfad nicht gefunden: {abs_path}{RESET}"

    _stop_event = threading.Event()
    _watch_thread = threading.Thread(
        target=_watch_loop,
        args=(path, instruction, agent_callback, thinking, max_tokens, interval, _stop_event),
        daemon=True,
        name="local-cli-watcher",
    )
    _watch_thread.start()
    return (
        f"{GREEN}Watch gestartet:{RESET} {abs_path}\n"
        f"{DIM}Anweisung: {instruction}\n"
        f"Intervall: {interval}s  |  /watch stop zum Beenden{RESET}"
    )


def stop() -> str:
    """Stop the running watcher."""
    global _stop_event, _watch_thread
    if _stop_event is None or not (_watch_thread and _watch_thread.is_alive()):
        return f"{DIM}Kein Watch-Mode aktiv.{RESET}"
    _stop_event.set()
    _watch_thread.join(timeout=5)
    _stop_event = None
    _watch_thread = None
    return f"{GREEN}Watch-Mode beendet.{RESET}"


def status() -> str:
    """Return current watcher status."""
    if _watch_thread and _watch_thread.is_alive():
        return f"{GREEN}Watch-Mode aktiv{RESET} — /watch stop zum Beenden."
    return f"{DIM}Watch-Mode nicht aktiv.{RESET}"
