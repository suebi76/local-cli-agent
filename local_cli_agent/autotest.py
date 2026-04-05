# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Steffen Schwabe
"""
autotest.py — Automatic test runner after every file write.

When enabled, runs a configured test command after every write_file /
edit_file tool call. The result (pass / fail + output) is appended to
the tool result so the agent sees it and can self-correct immediately.

No extra dependencies — uses subprocess.
"""
import subprocess

from local_cli_agent.constants import RESET, DIM, GREEN, RED, YELLOW

# ── State ────────────────────────────────────────────────────────────────────
_cmd: str | None = None


# ── Public API ───────────────────────────────────────────────────────────────
def enable(cmd: str) -> str:
    """Enable autotest with the given shell command."""
    global _cmd
    _cmd = cmd.strip()
    return f"{GREEN}Auto-Test aktiv:{RESET} {_cmd}"


def disable() -> str:
    """Disable autotest."""
    global _cmd
    _cmd = None
    return f"{DIM}Auto-Test deaktiviert.{RESET}"


def is_enabled() -> bool:
    return bool(_cmd)


def get_cmd() -> str | None:
    return _cmd


def run() -> tuple[bool, str]:
    """
    Run the configured test command.
    Returns (passed: bool, output: str).
    Output is capped at the last 60 lines to keep tool results lean.
    """
    if not _cmd:
        return True, ""
    print(f"\n{DIM}[autotest] {_cmd}{RESET}", flush=True)
    try:
        result = subprocess.run(
            _cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
            encoding="utf-8",
            errors="replace",
        )
        raw = (result.stdout + result.stderr).strip()
        passed = result.returncode == 0

        # Show last 30 lines in terminal
        lines = raw.splitlines()
        display = lines[-30:] if len(lines) > 30 else lines
        color = GREEN if passed else RED
        label = "PASSED" if passed else "FAILED"
        print(f" {color}[autotest] {label}{RESET}")
        for ln in display:
            print(f"  {DIM}{ln}{RESET}")

        # Return last 60 lines for the agent (keeps context window lean)
        agent_output = "\n".join(lines[-60:]) if len(lines) > 60 else raw
        return passed, agent_output

    except subprocess.TimeoutExpired:
        msg = "[autotest] Timeout nach 120 s — Tests abgebrochen."
        print(f"  {RED}{msg}{RESET}")
        return False, msg
    except Exception as e:
        msg = f"[autotest] Fehler: {e}"
        print(f"  {RED}{msg}{RESET}")
        return False, msg
