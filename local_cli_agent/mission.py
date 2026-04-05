# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Steffen Schwabe
"""
mission.py — Mission Mode for Local CLI Agent.

The user gives a high-level goal. The agent first produces a numbered
plan (up to 8 steps). The user confirms, then each step is executed
by a separate agent_loop call. After every step the user can pause
or abort. At the end a short summary is printed.

No extra dependencies.
"""
import json
import re

from local_cli_agent.constants import RESET, BOLD, DIM, CYAN, YELLOW, GREEN, RED

# Maximum steps in one mission
_MAX_STEPS = 8

# ── Plan extraction ───────────────────────────────────────────────────────────

def _parse_steps(content: str) -> list[str]:
    """
    Try to extract a list of steps from the agent's planning response.
    Accepts:
      1. JSON  {"steps": [...]}
      2. Numbered list  "1. Foo\n2. Bar"
    """
    if not content:
        return []

    # 1) JSON block
    for match in re.finditer(r'\{[^{}]*"steps"\s*:[^{}]*\}', content, re.DOTALL):
        try:
            data = json.loads(match.group())
            steps = data.get("steps", [])
            if isinstance(steps, list) and steps:
                return [str(s).strip() for s in steps[:_MAX_STEPS] if str(s).strip()]
        except json.JSONDecodeError:
            pass

    # 2) Numbered list fallback
    steps = []
    for line in content.splitlines():
        m = re.match(r'^\s*\d+[\.\)]\s+(.+)', line)
        if m:
            step = m.group(1).strip()
            if step:
                steps.append(step)
    return steps[:_MAX_STEPS]


# ── Main entry point ──────────────────────────────────────────────────────────

def run_mission(
    goal: str,
    messages: list,
    agent_callback,          # callable(messages, thinking, max_tokens) -> None
    thinking: bool = True,
    max_tokens: int = 4096,
) -> None:
    """
    Execute a mission:
    1. Ask the agent for a step-by-step plan (no tools, no streaming thought).
    2. Show the plan and ask for confirmation.
    3. Execute each step via agent_callback.
    4. Pause between steps (user can abort).
    5. Print a completion summary.
    """
    from local_cli_agent.api import call_api

    sep = "─" * 60

    # ── Step 1: Generate plan ─────────────────────────────────────────────
    print(f"\n{BOLD}{CYAN}[mission]{RESET} Erstelle Plan für: {CYAN}{goal}{RESET}")
    print(f"{DIM}{sep}{RESET}", flush=True)

    planning_messages = list(messages)   # shallow copy — keep system prompt
    planning_messages.append({
        "role": "user",
        "content": (
            f"MISSION: {goal}\n\n"
            "Erstelle einen Schritt-für-Schritt-Plan. "
            f"Maximal {_MAX_STEPS} Schritte. Antworte NUR mit:\n"
            '{"steps": ["Schritt 1", "Schritt 2", ...]}\n\n'
            "Kein erklärender Text außerhalb des JSON."
        ),
    })

    plan_content, _ = call_api(
        planning_messages,
        thinking=False,
        max_tokens=512,
        use_tools=False,
    )

    steps = _parse_steps(plan_content or "")
    if not steps:
        print(f"{RED}[mission] Konnte keinen Plan erstellen. "
              f"Antwort des Modells:\n{plan_content}{RESET}")
        return

    # ── Step 2: Show plan ─────────────────────────────────────────────────
    print(f"\n{BOLD}Mission:{RESET} {goal}")
    print(f"{DIM}{sep}{RESET}")
    for i, step in enumerate(steps, 1):
        print(f"  {CYAN}{i:>2}/{len(steps)}{RESET}  {step}")
    print(f"{DIM}{sep}{RESET}")

    try:
        confirm = input(
            f"\n{YELLOW}Mission starten?{RESET} "
            f"[{BOLD}Enter{RESET}] = ja  [{BOLD}n{RESET}] = abbrechen  "
        ).strip().lower()
    except (EOFError, KeyboardInterrupt):
        print(f"\n{DIM}Abgebrochen.{RESET}")
        return

    if confirm == "n":
        print(f"{DIM}[mission] Abgebrochen.{RESET}")
        return

    # ── Step 3: Execute steps ─────────────────────────────────────────────
    mission_messages = list(messages)   # fresh copy — starts clean
    completed = 0
    _MAX_HISTORY = 20  # max non-system messages kept to prevent context bloat

    for i, step in enumerate(steps, 1):
        print(f"\n{BOLD}{CYAN}[{i}/{len(steps)}]{RESET} {step}")
        print(f"{DIM}{sep}{RESET}", flush=True)

        # Trim history: keep system prompt + last _MAX_HISTORY messages
        sys_msgs = [m for m in mission_messages if m.get("role") == "system"]
        other_msgs = [m for m in mission_messages if m.get("role") != "system"]
        if len(other_msgs) > _MAX_HISTORY:
            other_msgs = other_msgs[-_MAX_HISTORY:]
            mission_messages = sys_msgs + other_msgs

        mission_messages.append({
            "role": "user",
            "content": (
                f"[Mission {i}/{len(steps)}] {step}\n\n"
                f"Gesamtziel: {goal}"
            ),
        })

        try:
            agent_callback(
                mission_messages,
                thinking=thinking,
                max_tokens=max_tokens,
            )
        except KeyboardInterrupt:
            print(f"\n{YELLOW}[mission] Unterbrochen bei Schritt {i}.{RESET}")
            break
        except Exception as e:
            print(f"\n{RED}[mission] Fehler in Schritt {i}: {e}{RESET}")
            try:
                cont = input(f"{YELLOW}Trotzdem weitermachen? [Enter / n]{RESET} ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                break
            if cont == "n":
                break

        completed += 1

        # Pause between steps (not after the last one)
        if i < len(steps):
            try:
                choice = input(
                    f"\n{DIM}[mission] Schritt {i} fertig. "
                    f"Weiter mit Schritt {i + 1}? "
                    f"[{BOLD}Enter{RESET}] = ja  [{BOLD}s{RESET}] = stopp{DIM}  {RESET}"
                ).strip().lower()
            except (EOFError, KeyboardInterrupt):
                print(f"\n{YELLOW}[mission] Gestoppt.{RESET}")
                break
            if choice == "s":
                print(f"{YELLOW}[mission] Gestoppt nach Schritt {i}/{len(steps)}.{RESET}")
                break

    # ── Summary ───────────────────────────────────────────────────────────
    print(f"\n{DIM}{sep}{RESET}")
    if completed == len(steps):
        print(f"{GREEN}{BOLD}Mission abgeschlossen!{RESET} "
              f"{GREEN}({completed}/{len(steps)} Schritte erledigt){RESET}")
    else:
        print(f"{YELLOW}Mission beendet: {completed}/{len(steps)} Schritte abgeschlossen.{RESET}")
    print()
