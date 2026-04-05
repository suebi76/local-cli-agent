# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Steffen Schwabe
"""
orchestrator.py — Master-Orchestrator for Local CLI Agent.

For complex tasks the orchestrator:
  1. Detects task complexity automatically (or is started explicitly).
  2. Asks a master-LLM to produce a step-by-step plan where each step is
     assigned to the most suitable specialist profile.
  3. Shows the plan to the user for confirmation / editing.
  4. Executes each step by temporarily switching to the assigned profile and
     calling agent_loop with full context from previous steps.
  5. Automatically inserts a verification step when code is being written.
  6. Restores the original profile afterwards.

No extra dependencies — uses the existing profiles, config and api modules.
"""
import json
import re

from local_cli_agent.constants import RESET, BOLD, DIM, CYAN, YELLOW, GREEN, RED, MAGENTA

# ── Constants ─────────────────────────────────────────────────────────────────
_MAX_STEPS = 10
_COMPLEXITY_THRESHOLD = 0.55   # score ≥ this → suggest orchestrator
_SUMMARY_MAX_CHARS = 400        # chars of each step summary passed to next step

# ── Complexity keywords (DE + EN) ─────────────────────────────────────────────
_COMPLEX_KEYWORDS = [
    # German
    "komplett", "vollständig", "vollständiges", "ganzes", "ganzen",
    "system", "anwendung", "applikation", "plattform",
    "baue mir", "baue", "erstelle mir", "erstelle ein", "implementiere",
    "inklusive", "inkl", "einschließlich", "sowie",
    "mit tests", "mit dokumentation", "mit authentifizierung",
    "datenbank", "authentifizierung", "autorisierung",
    # English
    "complete", "full", "entire", "whole",
    "build me", "build a", "create a", "implement",
    "with tests", "with documentation", "with authentication",
    "database", "authentication", "authorization",
    "rest api", "rest-api", "graphql", "microservice",
]

# Multi-concern signals (each adds to score)
_CONJUNCTION_SIGNALS = ["und ", "sowie ", "außerdem", "inkl", "including", " and "]

# ── Specialist keyword mapping (fallback when LLM picks no specialist) ────────
_SPECIALIST_KEYWORDS: dict[str, list[str]] = {
    "architect":    ["struktur", "schema", "architektur", "design", "entwerfen", "planen",
                     "modell", "diagram"],
    "backend":      ["api", "route", "endpoint", "server", "datenbank", "database",
                     "model", "controller", "auth", "login", "registrier", "crud"],
    "frontend":     ["html", "css", "javascript", "js", "ui", "interface", "seite",
                     "komponente", "layout", "responsiv", "design"],
    "tester":       ["test", "tests", "unittest", "integration", "coverage", "abdeckung"],
    "security":     ["sicherheit", "schwachstell", "vulnerab", "csrf", "xss",
                     "injection", "sanitiz", "validier"],
    "docs":         ["dokumentation", "readme", "kommentar", "docstring", "beschreibung"],
    "devops":       ["docker", "deploy", "ci", "cd", "kubernetes", "nginx", "server"],
    "performance":  ["performance", "optimier", "schnell", "cache", "index"],
    "debugger":     ["fehler", "bug", "reparier", "fix", "absturz", "exception"],
    "verifikation": ["prüf", "verifi", "smoke", "funktioniert", "läuft"],
}

# Steps that produce code and should be followed by verification
_CODE_SPECIALISTS = {"backend", "frontend", "tester", "architect"}


# ── Complexity detection ──────────────────────────────────────────────────────

def _complexity_score(prompt: str) -> float:
    """Return a 0.0–1.0 complexity score for the given prompt."""
    pl = prompt.lower()
    words = prompt.split()
    score = 0.0

    # Length signal
    if len(words) > 15:
        score += 0.30
    if len(words) > 30:
        score += 0.20

    # Keyword hits
    hits = sum(1 for kw in _COMPLEX_KEYWORDS if kw in pl)
    score += min(hits * 0.15, 0.50)

    # Multi-concern conjunctions
    conj = sum(1 for c in _CONJUNCTION_SIGNALS if c in pl)
    score += min(conj * 0.10, 0.20)

    return min(score, 1.0)


def should_suggest(prompt: str) -> bool:
    """Return True when the orchestrator should be offered to the user."""
    if prompt.startswith("/"):
        return False
    return _complexity_score(prompt) >= _COMPLEXITY_THRESHOLD


# ── Specialist inference (fallback) ──────────────────────────────────────────

def _infer_specialist(step: str) -> str:
    """Guess the best specialist for a step based on keywords."""
    sl = step.lower()
    best, best_hits = "standard", 0
    for spec, keywords in _SPECIALIST_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in sl)
        if hits > best_hits:
            best, best_hits = spec, hits
    return best


# ── Plan parsing ──────────────────────────────────────────────────────────────

def _parse_plan(content: str) -> list[dict]:
    """
    Parse orchestration plan from LLM response.
    Accepts {"specialists": [{"step": ..., "specialist": ...}, ...]}
    or falls back to numbered list + keyword inference.
    Returns list of {"step": str, "specialist": str}.
    """
    if not content:
        return []

    # JSON block
    for m in re.finditer(r'\{[^{}]*"specialists"\s*:[^{}]*\}', content, re.DOTALL):
        try:
            data = json.loads(m.group())
            items = data.get("specialists", [])
            if isinstance(items, list) and items:
                result = []
                for it in items[:_MAX_STEPS]:
                    step = str(it.get("step", "")).strip()
                    spec = str(it.get("specialist", "")).strip().lower()
                    if step:
                        if spec not in _SPECIALIST_KEYWORDS and spec != "standard":
                            spec = _infer_specialist(step)
                        result.append({"step": step, "specialist": spec})
                if result:
                    return result
        except json.JSONDecodeError:
            pass

    # Numbered-list fallback
    result = []
    for line in content.splitlines():
        m = re.match(r'^\s*\d+[\.\)]\s+(.+)', line)
        if m:
            step = m.group(1).strip()
            if step:
                result.append({"step": step, "specialist": _infer_specialist(step)})
    return result[:_MAX_STEPS]


# ── Profile emoji lookup ──────────────────────────────────────────────────────

def _profile_label(specialist: str) -> str:
    from local_cli_agent.profiles import PROFILES
    p = PROFILES.get(specialist)
    if p:
        return f"{p.emoji} {p.label}"
    return f"🤖 {specialist.capitalize()}"


# ── Verification auto-insert ──────────────────────────────────────────────────

def _ensure_verification(plan: list[dict]) -> list[dict]:
    """
    If the plan contains code-producing steps and no verification step,
    insert a verification step before the docs step (or at the end).
    """
    has_code = any(s["specialist"] in _CODE_SPECIALISTS for s in plan)
    has_verif = any(s["specialist"] == "verifikation" for s in plan)
    if not has_code or has_verif:
        return plan

    verif = {"step": "Prüfen ob alles funktioniert (Tests ausführen, Imports verifizieren)", "specialist": "verifikation"}

    # Insert before docs step if present
    for i, s in enumerate(plan):
        if s["specialist"] == "docs":
            return plan[:i] + [verif] + plan[i:]
    return plan + [verif]


# ── Main orchestration ────────────────────────────────────────────────────────

def run_orchestration(
    goal: str,
    messages: list,
    agent_callback,          # callable(messages, thinking, max_tokens) -> None
    thinking: bool = True,
    max_tokens: int = 4096,
) -> None:
    """
    Full orchestration cycle:
    1. Generate specialist plan via master LLM call
    2. Show plan + ask user to confirm
    3. Execute each step with the assigned specialist profile
    4. Pass context summaries between steps
    5. Restore original profile
    """
    from local_cli_agent.api import call_api
    from local_cli_agent.config import build_system_prompt
    from local_cli_agent import profiles as _profiles
    from local_cli_agent import autotest as _autotest

    sep = "─" * 64
    original_profile_id = _profiles.get_active().id

    # ── Step 1: Generate plan ─────────────────────────────────────────
    print(f"\n{BOLD}{MAGENTA}[orchestrator]{RESET} Analysiere Aufgabe und erstelle Plan...")
    print(f"{DIM}{sep}{RESET}", flush=True)

    planning_messages = list(messages)
    planning_messages.append({
        "role": "user",
        "content": (
            f"AUFGABE: {goal}\n\n"
            f"Erstelle einen Orchestrierungsplan. Maximal {_MAX_STEPS} Schritte.\n"
            "Weise jedem Schritt den besten Spezialisten zu.\n\n"
            "Verfügbare Spezialisten: architect, backend, frontend, tester, "
            "security, docs, devops, performance, debugger, verifikation, standard\n\n"
            "Antworte NUR mit diesem JSON (kein Text davor oder danach):\n"
            '{"specialists": [\n'
            '  {"step": "Was zu tun ist", "specialist": "spezialist-id"},\n'
            '  ...\n'
            ']}'
        ),
    })

    plan_content, _ = call_api(
        planning_messages,
        thinking=False,
        max_tokens=800,
        use_tools=False,
    )

    plan = _parse_plan(plan_content or "")
    if not plan:
        print(f"{RED}[orchestrator] Plan konnte nicht erstellt werden.{RESET}")
        if plan_content:
            print(f"{DIM}Modell-Antwort: {plan_content[:300]}{RESET}")
        return

    plan = _ensure_verification(plan)

    # ── Step 2: Show plan ─────────────────────────────────────────────
    print(f"\n{BOLD}Orchestrierung:{RESET} {goal}")
    print(f"{DIM}{sep}{RESET}")
    for i, s in enumerate(plan, 1):
        label = _profile_label(s["specialist"])
        print(f"  {CYAN}{i:>2}/{len(plan)}{RESET}  {label:<28}  {DIM}{s['step']}{RESET}")
    print(f"{DIM}{sep}{RESET}")

    try:
        confirm = input(
            f"\n{YELLOW}Orchestrierung starten?{RESET} "
            f"[{BOLD}Enter{RESET}] = ja  "
            f"[{BOLD}n{RESET}] = abbrechen  "
            f"[{BOLD}e{RESET}] = Schritte bearbeiten  "
        ).strip().lower()
    except (EOFError, KeyboardInterrupt):
        print(f"\n{DIM}Abgebrochen.{RESET}")
        return

    if confirm == "n":
        print(f"{DIM}[orchestrator] Abgebrochen.{RESET}")
        return

    if confirm == "e":
        plan = _edit_plan(plan)
        if not plan:
            print(f"{DIM}[orchestrator] Abgebrochen.{RESET}")
            return

    # ── Step 3: Execute ───────────────────────────────────────────────
    summaries: list[str] = []
    completed = 0

    for i, step_info in enumerate(plan, 1):
        specialist = step_info["specialist"]
        step_text = step_info["step"]
        label = _profile_label(specialist)

        print(f"\n{BOLD}{MAGENTA}[{i}/{len(plan)}]{RESET} {label}")
        print(f"{DIM}{step_text}{RESET}")
        print(f"{DIM}{sep}{RESET}", flush=True)

        # Switch profile temporarily
        _profiles.set_profile(specialist)

        # Build context message
        context_parts = [f"[Orchestrierung Schritt {i}/{len(plan)} — {label}]"]
        context_parts.append(f"Gesamtziel: {goal}")
        if summaries:
            context_parts.append("\nBisherige Ergebnisse:")
            for j, (prev_step, summary) in enumerate(
                zip([s["step"] for s in plan[:i-1]], summaries), 1
            ):
                spec_label = _profile_label(plan[j-1]["specialist"])
                context_parts.append(f"  Schritt {j} ({spec_label}): {summary[:_SUMMARY_MAX_CHARS]}")
        context_parts.append(f"\nDeine Aufgabe: {step_text}")

        step_messages = [
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": "\n".join(context_parts)},
        ]

        # Execute
        step_summary = ""
        try:
            agent_callback(step_messages, thinking=thinking, max_tokens=max_tokens)

            # Extract summary from last assistant message
            for msg in reversed(step_messages):
                if msg.get("role") == "assistant" and msg.get("content"):
                    step_summary = msg["content"][:_SUMMARY_MAX_CHARS]
                    break

            # Run autotest after code steps
            if _autotest.is_enabled() and specialist in _CODE_SPECIALISTS:
                passed, _ = _autotest.run()
                if not passed:
                    step_summary += " [autotest: FEHLGESCHLAGEN]"

        except KeyboardInterrupt:
            print(f"\n{YELLOW}[orchestrator] Unterbrochen bei Schritt {i}.{RESET}")
            break
        except Exception as e:
            print(f"\n{RED}[orchestrator] Fehler in Schritt {i}: {e}{RESET}")
            try:
                choice = input(
                    f"{YELLOW}[r]etry / [s]kip / [a]bort?{RESET} "
                ).strip().lower()
            except (EOFError, KeyboardInterrupt):
                break
            if choice == "r":
                # retry same step
                i -= 1
                continue
            elif choice == "a":
                break
            # skip: continue to next

        summaries.append(step_summary or f"Schritt {i} abgeschlossen.")
        completed += 1

        # Pause between steps
        if i < len(plan):
            try:
                choice = input(
                    f"\n{DIM}[orchestrator] Schritt {i} fertig. "
                    f"Weiter mit {_profile_label(plan[i]['specialist'])}? "
                    f"[{BOLD}Enter{RESET}]{DIM} = ja  "
                    f"[{BOLD}s{RESET}] = stopp{RESET}  "
                ).strip().lower()
            except (EOFError, KeyboardInterrupt):
                break
            if choice == "s":
                print(f"{YELLOW}[orchestrator] Gestoppt nach Schritt {i}/{len(plan)}.{RESET}")
                break

    # ── Restore original profile ──────────────────────────────────────
    _profiles.set_profile(original_profile_id)

    # ── Summary ───────────────────────────────────────────────────────
    print(f"\n{DIM}{sep}{RESET}")
    if completed == len(plan):
        print(f"{GREEN}{BOLD}Orchestrierung abgeschlossen!{RESET} "
              f"{GREEN}{completed}/{len(plan)} Schritte erledigt.{RESET}")
    else:
        print(f"{YELLOW}Orchestrierung beendet: {completed}/{len(plan)} Schritte abgeschlossen.{RESET}")
    print()


# ── Interactive plan editor ───────────────────────────────────────────────────

def _edit_plan(plan: list[dict]) -> list[dict]:
    """Let the user edit the plan interactively before execution."""
    from local_cli_agent.profiles import PROFILES

    print(f"\n{BOLD}Plan bearbeiten{RESET} — Schritt-Nummer eingeben um ihn zu ändern, "
          f"'ok' wenn fertig:\n")

    while True:
        for i, s in enumerate(plan, 1):
            label = _profile_label(s["specialist"])
            print(f"  {CYAN}{i:>2}{RESET}  {label:<28}  {s['step']}")
        print(f"  {DIM}+   Schritt hinzufügen{RESET}")
        print(f"  {DIM}-N  Schritt N löschen (z.B. -3){RESET}")
        print(f"  {DIM}ok  Fertig{RESET}\n")

        try:
            raw = input(f"{YELLOW}>{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            return []

        if raw.lower() in ("ok", ""):
            return plan

        # Delete step
        if raw.startswith("-"):
            try:
                idx = int(raw[1:]) - 1
                if 0 <= idx < len(plan):
                    removed = plan.pop(idx)
                    print(f"{DIM}Entfernt: {removed['step']}{RESET}\n")
                else:
                    print(f"{RED}Ungültige Nummer.{RESET}\n")
            except ValueError:
                print(f"{RED}Format: -N (z.B. -3){RESET}\n")
            continue

        # Add step
        if raw == "+":
            try:
                new_step = input("  Schritt-Beschreibung: ").strip()
                spec_ids = list(PROFILES.keys())
                print(f"  Spezialist ({', '.join(spec_ids)}): ", end="")
                new_spec = input().strip().lower()
                if new_spec not in PROFILES:
                    new_spec = "standard"
                plan.append({"step": new_step, "specialist": new_spec})
                print(f"{DIM}Hinzugefügt.{RESET}\n")
            except (EOFError, KeyboardInterrupt):
                pass
            continue

        # Edit step by number
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(plan):
                s = plan[idx]
                print(f"  Aktuell: {s['step']}")
                new_step = input("  Neuer Text (Enter = unverändert): ").strip()
                spec_ids = list(PROFILES.keys())
                print(f"  Spezialist (aktuell: {s['specialist']}, Enter = unverändert): ", end="")
                new_spec = input().strip().lower()
                if new_step:
                    plan[idx]["step"] = new_step
                if new_spec and new_spec in PROFILES:
                    plan[idx]["specialist"] = new_spec
                print(f"{DIM}Aktualisiert.{RESET}\n")
            else:
                print(f"{RED}Ungültige Nummer.{RESET}\n")
        except ValueError:
            print(f"{RED}Nummer, '+', '-N' oder 'ok' eingeben.{RESET}\n")
