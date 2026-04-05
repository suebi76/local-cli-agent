# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Steffen Schwabe
import os
import sys
from datetime import datetime

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.history import InMemoryHistory

from local_cli_agent.constants import (
    RESET, BOLD, DIM, CYAN, GREEN, YELLOW, MAGENTA, RED, BLUE,
    VERSION, SCRIPT_FILE,
)
from local_cli_agent.config import build_system_prompt
from local_cli_agent.api import get_model_name, call_api
from local_cli_agent.memory import load_memory
from local_cli_agent.changelog import get_changelog
from local_cli_agent.agent import agent_loop
from local_cli_agent import undo as _undo
from local_cli_agent import watcher as _watcher
from local_cli_agent import autotest as _autotest
from local_cli_agent import mission as _mission
from local_cli_agent import profiles as _profiles
from local_cli_agent import orchestrator as _orchestrator
from local_cli_agent import settings as _settings
import local_cli_agent.executor as executor

_SLASH_COMMANDS = [
    "/auto", "/clear", "/cd", "/compact", "/memory",
    "/model", "/profile", "/history", "/tokens", "/save",
    "/undo", "/checkpoint",
    "/mission", "/orchestrate",
    "/autotest",
    "/watch",
    "/reload", "/version", "/changelog", "/help", "/quit",
]

_CMD_META = {
    "/auto":       "Auto-approve ein/aus",
    "/clear":      "Konversationsverlauf löschen",
    "/cd":         "Arbeitsverzeichnis wechseln",
    "/compact":    "Konversation komprimieren (spart Tokens)",
    "/memory":     "Gespeicherte Erinnerungen anzeigen",
    "/model":      "Modell wechseln",
    "/profile":    "Agenten-Persönlichkeit wechseln  z.B. /profile aufraumen",
    "/history":    "Nachrichtenverlauf anzeigen",
    "/tokens":     "Max. Output-Tokens setzen  z.B. /tokens 8192",
    "/save":       "Konversation als Markdown speichern",
    "/undo":       "Letzte Dateiänderung rückgängig  z.B. /undo 3",
    "/checkpoint": "Manuellen Rückgabepunkt setzen",
    "/mission":    "Mehrstufige Mission starten  z.B. /mission Refaktoriere alle API-Endpunkte",
    "/orchestrate": "Master-Orchestrator: mehrere Spezialisten für komplexe Aufgaben",
    "/autotest":   "Tests nach jeder Dateiänderung automatisch ausführen",
    "/watch":      "Dateien beobachten und Agent automatisch auslösen",
    "/reload":     "Nach Self-Improvement neu laden",
    "/version":    "Versionsinformationen",
    "/changelog":  "Self-Improvement-Verlauf",
    "/help":       "Diese Hilfe anzeigen",
    "/quit":       "Beenden",
}


class _SlashCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if not text.startswith("/"):
            return
        word = text.split()[0] if text.split() else text
        for cmd in _SLASH_COMMANDS:
            if cmd.startswith(word):
                yield Completion(cmd, start_position=-len(word), display_meta=_CMD_META.get(cmd, ""))


def print_banner():
    """Print the startup banner."""
    model_label = get_model_name() or "kein Modell"
    sep = "=" * 66
    print(f"""
{BOLD}{CYAN}{sep}
  Local CLI Agent v{VERSION}
  Self-improving AI coding assistant
{GREEN}  Modell: {model_label}{RESET}
{BOLD}{CYAN}{sep}{RESET}
{DIM}Tools: bash  |  dateien  |  edit  |  grep  |  glob  |  web  |  memory  |  self-improve{RESET}

{DIM}Commands:{RESET}
  {YELLOW}/auto on|off{RESET}      Tool-Ausfuehrung auto-bestaetigen
  {YELLOW}/clear{RESET}            Konversationsverlauf loeschen
  {YELLOW}/cd <path>{RESET}        Arbeitsverzeichnis wechseln
  {YELLOW}/compact{RESET}          Konversation komprimieren (spart Tokens)
  {YELLOW}/model{RESET}            Modell wechseln ohne Neustart
  {YELLOW}/profile{RESET}          Agenten-Persoenlichkeit wechseln (14 Profile)
  {YELLOW}/save{RESET}             Konversation als Markdown speichern
  {YELLOW}/memory{RESET}           Gespeicherte Erinnerungen anzeigen
  {YELLOW}/history{RESET}          Nachrichtenverlauf anzeigen
  {YELLOW}/tokens <n>{RESET}       Max. Tokens setzen (z.B. /tokens 8192)
  {YELLOW}/undo [n]{RESET}          Letzte n Dateiänderungen rückgängig machen
  {YELLOW}/checkpoint [name]{RESET} Manuellen Rückgabepunkt setzen
  {YELLOW}/mission <ziel>{RESET}    Mehrstufige Mission (Agent plant + fuehrt aus)
  {YELLOW}/orchestrate <ziel>{RESET} Mehrere Spezialisten orchestrieren (komplex)
  {YELLOW}/autotest <cmd>{RESET}    Tests nach jeder Aenderung automatisch ausfuehren
  {YELLOW}/autotest off{RESET}      Auto-Test deaktivieren
  {YELLOW}/watch <pfad> <anweisung>{RESET}  Dateien beobachten (Agent auto-auslösen)
  {YELLOW}/watch stop{RESET}        Watch-Mode beenden
  {YELLOW}/watch status{RESET}      Watch-Status anzeigen
  {YELLOW}/reload{RESET}            Nach Self-Improvement neu laden
  {YELLOW}/version{RESET}           Versionsinformationen
  {YELLOW}/changelog{RESET}        Self-Improvement-Verlauf
  {YELLOW}/help{RESET}             Diese Hilfe anzeigen
  {YELLOW}/quit{RESET}             Beenden (oder Ctrl+C)

{DIM}Tipp: 'a' beim Tool-Prompt druecken = alle auto-bestaetigen.{RESET}
""")


def interactive_mode(thinking=True, system_prompt=None, max_tokens=None):
    """Run interactive chat loop."""
    # ── Load persisted settings ───────────────────────────────────────────
    _saved = _settings.load()
    if max_tokens is None:
        max_tokens = _saved.get("max_tokens", 4096)
    saved_profile = _saved.get("active_profile", "standard")
    if saved_profile != "standard":
        _profiles.set_profile(saved_profile)
    saved_autotest = _saved.get("autotest_cmd")
    if saved_autotest:
        _autotest.enable(saved_autotest)

    print_banner()

    messages = [{"role": "system", "content": build_system_prompt(system_prompt)}]

    auto_str = f"{GREEN}on{RESET}" if executor.auto_approve else f"{RED}off{RESET}"
    active_p = _profiles.get_active()
    profile_str = f"{active_p.emoji} {active_p.label}" if active_p.id != "standard" else "Standard"
    print(f"{DIM}Auto-approve: {auto_str} {DIM}| Tokens: {max_tokens} | Profil: {profile_str}{RESET}")
    print(f"{DIM}CWD: {os.getcwd()}{RESET}\n")

    session = PromptSession(
        completer=_SlashCompleter(),
        history=InMemoryHistory(),
        complete_while_typing=True,
    )

    while True:
        try:
            lines = []
            while True:
                prompt_str = ANSI(f"\n{BOLD}{CYAN}You:{RESET} ") if not lines else ANSI(f" {DIM}...{RESET} ")
                line = session.prompt(prompt_str)
                if line == "" and lines:
                    break
                if line == "" and not lines:
                    continue
                lines.append(line)
                if len(lines) == 1 and not line.endswith("\\"):
                    break
                if line.endswith("\\"):
                    lines[-1] = line[:-1]
            user_input = "\n".join(lines).strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n\n{DIM}Goodbye!{RESET}")
            break

        if not user_input:
            continue

        # ── Handle slash commands ─────────────────────────────────────────
        if user_input.startswith("/"):
            cmd = user_input.split()
            cmd_lower = cmd[0].lower()

            # ── /quit ──────────────────────────────────────────────────────
            if cmd_lower in ("/quit", "/exit", "/q"):
                print(f"\n{DIM}Goodbye!{RESET}")
                break

            # ── /clear ─────────────────────────────────────────────────────
            elif cmd_lower == "/clear":
                messages = [{"role": "system", "content": build_system_prompt(system_prompt)}]
                print(f"{DIM}Konversation gelöscht.{RESET}\n")

            # ── /auto ──────────────────────────────────────────────────────
            elif cmd_lower == "/auto":
                if len(cmd) > 1 and cmd[1].lower() in ("on", "off"):
                    executor.auto_approve = cmd[1].lower() == "on"
                else:
                    executor.auto_approve = not executor.auto_approve
                auto_str = f"{GREEN}on{RESET}" if executor.auto_approve else f"{RED}off{RESET}"
                print(f"{DIM}Auto-approve: {auto_str}{RESET}\n")

            # ── /cd ────────────────────────────────────────────────────────
            elif cmd_lower == "/cd":
                if len(cmd) > 1:
                    new_dir = " ".join(cmd[1:])
                    try:
                        os.chdir(new_dir)
                        messages[0]["content"] = build_system_prompt(system_prompt)
                        print(f"{DIM}CWD: {os.getcwd()}{RESET}\n")
                    except Exception as e:
                        print(f"{RED}Fehler: {e}{RESET}\n")
                else:
                    print(f"{DIM}CWD: {os.getcwd()}{RESET}\n")

            # ── /tokens ────────────────────────────────────────────────────
            elif cmd_lower == "/tokens":
                if len(cmd) > 1:
                    try:
                        max_tokens = int(cmd[1])
                        _settings.set_value("max_tokens", max_tokens)
                        print(f"{DIM}Max Tokens gesetzt: {max_tokens} (gespeichert){RESET}\n")
                    except ValueError:
                        print(f"{RED}Ungültige Zahl. Beispiel: /tokens 8192{RESET}\n")
                else:
                    print(f"{DIM}Aktuell: {max_tokens} Tokens  |  Ändern mit: /tokens 8192{RESET}\n")

            # ── /memory ────────────────────────────────────────────────────
            elif cmd_lower == "/memory":
                mem = load_memory()
                if not mem:
                    print(f"{DIM}Keine Erinnerungen gespeichert.{RESET}\n")
                else:
                    for k, v in mem.items():
                        preview = v["content"][:80].replace("\n", " ")
                        print(f" {CYAN}{k}{RESET}: {DIM}{preview}{RESET}")
                    print()

            # ── /history ───────────────────────────────────────────────────
            elif cmd_lower == "/history":
                count = 0
                for msg in messages:
                    role = msg.get("role", "")
                    if role == "system":
                        continue
                    content = msg.get("content", "") or ""
                    if role == "user":
                        print(f" {CYAN}[du]    {content[:80]}{RESET}")
                        count += 1
                    elif role == "assistant":
                        tc = msg.get("tool_calls")
                        if tc:
                            names = ", ".join(t["function"]["name"] for t in tc)
                            print(f" {GREEN}[agent] {content[:60]} [tools: {names}]{RESET}")
                        else:
                            print(f" {GREEN}[agent] {content[:80]}{RESET}")
                        count += 1
                    elif role == "tool":
                        print(f" {DIM}[tool]  {content[:60]}...{RESET}")
                if count == 0:
                    print(f"{DIM}Noch keine Nachrichten.{RESET}")
                print()

            # ── /save ──────────────────────────────────────────────────────
            elif cmd_lower == "/save":
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"session_{timestamp}.md"
                filepath = os.path.join(os.getcwd(), filename)
                lines_out = [
                    f"# Local CLI Agent – Session {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n",
                    f"**Modell:** {get_model_name()}  \n",
                    f"**Verzeichnis:** {os.getcwd()}\n\n---\n\n",
                ]
                for msg in messages:
                    role = msg.get("role", "")
                    content = msg.get("content", "") or ""
                    if role == "system":
                        continue
                    elif role == "user":
                        lines_out.append(f"## Du\n\n{content}\n\n")
                    elif role == "assistant":
                        tc = msg.get("tool_calls")
                        if content:
                            lines_out.append(f"## Agent\n\n{content}\n\n")
                        if tc:
                            for t in tc:
                                lines_out.append(
                                    f"> **Tool:** `{t['function']['name']}`\n\n"
                                )
                    elif role == "tool":
                        lines_out.append(f"> Tool-Ergebnis: {content[:300]}\n\n")
                try:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.writelines(lines_out)
                    print(f"{GREEN}Gespeichert: {filepath}{RESET}\n")
                except Exception as e:
                    print(f"{RED}Fehler: {e}{RESET}\n")

            # ── /model ─────────────────────────────────────────────────────
            elif cmd_lower == "/model":
                from local_cli_agent import model_selector
                from local_cli_agent import api as _api
                from local_cli_agent.config import save_last_model
                entry = model_selector.show_selector()
                if entry:
                    save_last_model(f"{entry.backend}:{entry.model_id}")
                    _api.set_entry(entry)
                    messages[0]["content"] = build_system_prompt(system_prompt)
                    print(f"{GREEN}Modell gewechselt: {entry.name}{RESET}\n")
                else:
                    print(f"{DIM}Abgebrochen.{RESET}\n")

            # ── /profile ──────────────────────────────────────────────────
            elif cmd_lower == "/profile":
                if len(cmd) > 1:
                    pid = cmd[1].lower()
                    chosen = _profiles.set_profile(pid)
                    if chosen:
                        _settings.set_value("active_profile", chosen.id)
                        messages[0]["content"] = build_system_prompt(system_prompt)
                        if chosen.id == "standard":
                            print(f"{DIM}Profil zurückgesetzt: Standard (gespeichert){RESET}\n")
                        else:
                            print(f"{GREEN}Profil aktiv: {chosen.emoji} {chosen.label} (gespeichert){RESET}")
                            print(f"{DIM}{chosen.tagline}{RESET}\n")
                    else:
                        ids = ", ".join(_profiles.PROFILES.keys())
                        print(f"{RED}Unbekanntes Profil '{cmd[1]}'.{RESET} "
                              f"Verfügbar: {ids}\n")
                else:
                    chosen = _profiles.show_selector()
                    if chosen:
                        _settings.set_value("active_profile", chosen.id)
                        messages[0]["content"] = build_system_prompt(system_prompt)
                        if chosen.id == "standard":
                            print(f"{DIM}Profil zurückgesetzt: Standard (gespeichert){RESET}\n")
                        else:
                            print(f"\n{GREEN}Profil aktiv: {chosen.emoji} {chosen.label} (gespeichert){RESET}\n")

            # ── /compact ───────────────────────────────────────────────────
            elif cmd_lower == "/compact":
                non_sys = [m for m in messages if m.get("role") != "system"]
                if len(non_sys) < 4:
                    print(f"{DIM}Zu wenig Nachrichten zum Komprimieren (min. 4).{RESET}\n")
                    continue
                print(f"{DIM}Komprimiere {len(non_sys)} Nachrichten...{RESET}", flush=True)
                try:
                    summary_msgs = messages + [{
                        "role": "user",
                        "content": (
                            "Fasse die bisherige Konversation in 3-5 Sätzen zusammen. "
                            "Halte wichtige Fakten, Entscheidungen und den aktuellen Stand fest. "
                            "Antworte NUR mit der Zusammenfassung, ohne Einleitung."
                        ),
                    }]
                    content, _ = call_api(summary_msgs, thinking=False, max_tokens=512, use_tools=False)
                    if content:
                        messages = [
                            {"role": "system", "content": build_system_prompt(system_prompt)},
                            {"role": "assistant", "content": f"[Zusammenfassung der bisherigen Konversation]: {content}"},
                        ]
                        print(f"{GREEN}Konversation auf 1 Nachricht komprimiert.{RESET}\n")
                    else:
                        print(f"{RED}Komprimierung fehlgeschlagen (leere Antwort).{RESET}\n")
                except Exception as e:
                    print(f"{RED}Komprimierung fehlgeschlagen: {e}{RESET}\n")

            # ── /undo ──────────────────────────────────────────────────────
            elif cmd_lower == "/undo":
                n = 1
                if len(cmd) > 1:
                    try:
                        n = int(cmd[1])
                    except ValueError:
                        print(f"{RED}Ungültige Zahl. Beispiel: /undo 3{RESET}\n")
                        continue
                if _undo.size() == 0:
                    print(f"{DIM}Undo-Verlauf ist leer.{RESET}\n")
                else:
                    result = _undo.undo(n)
                    print(f"{GREEN}{result}{RESET}\n")

            # ── /checkpoint ────────────────────────────────────────────────
            elif cmd_lower == "/checkpoint":
                label = " ".join(cmd[1:]) if len(cmd) > 1 else "manuell"
                result = _undo.save_manual_checkpoint(label)
                print(f"{DIM}{result}{RESET}\n")

            # ── /mission ──────────────────────────────────────────────────
            elif cmd_lower == "/mission":
                goal = " ".join(cmd[1:]).strip()
                if not goal:
                    print(f"{DIM}Verwendung: /mission <Ziel>{RESET}\n"
                          f"  Beispiel: {YELLOW}/mission Refaktoriere alle API-Endpunkte auf async/await{RESET}\n")
                else:
                    try:
                        _mission.run_mission(
                            goal=goal,
                            messages=messages,
                            agent_callback=agent_loop,
                            thinking=thinking,
                            max_tokens=max_tokens,
                        )
                    except Exception as e:
                        print(f"{RED}Mission abgebrochen: {e}{RESET}\n")

            # ── /orchestrate ───────────────────────────────────────────────
            elif cmd_lower == "/orchestrate":
                goal = " ".join(cmd[1:]).strip()
                if not goal:
                    print(f"{DIM}Verwendung: /orchestrate <Ziel>{RESET}\n"
                          f"  Beispiel: {YELLOW}/orchestrate Baue eine REST-API für ein Blog-System{RESET}\n")
                else:
                    try:
                        _orchestrator.run_orchestration(
                            goal=goal,
                            messages=messages,
                            agent_callback=agent_loop,
                            thinking=thinking,
                            max_tokens=max_tokens,
                        )
                    except Exception as e:
                        print(f"{RED}Orchestrierung abgebrochen: {e}{RESET}\n")

            # ── /autotest ─────────────────────────────────────────────────
            elif cmd_lower == "/autotest":
                if len(cmd) < 2:
                    if _autotest.is_enabled():
                        print(f"{DIM}Auto-Test aktiv:{RESET} {YELLOW}{_autotest.get_cmd()}{RESET}\n"
                              f"  {DIM}Deaktivieren mit: /autotest off{RESET}\n")
                    else:
                        print(f"{DIM}Auto-Test inaktiv.{RESET}\n"
                              f"  Beispiel: {YELLOW}/autotest pytest tests/{RESET}\n")
                elif cmd[1].lower() == "off":
                    _settings.set_value("autotest_cmd", None)
                    print(_autotest.disable())
                else:
                    test_cmd = " ".join(cmd[1:])
                    _settings.set_value("autotest_cmd", test_cmd)
                    print(_autotest.enable(test_cmd))
                print()

            # ── /watch ────────────────────────────────────────────────────
            elif cmd_lower == "/watch":
                if len(cmd) < 2:
                    print(f"{DIM}Verwendung:{RESET}\n"
                          f"  {YELLOW}/watch <pfad> <anweisung>{RESET}  — Watch starten\n"
                          f"  {YELLOW}/watch stop{RESET}                 — Watch beenden\n"
                          f"  {YELLOW}/watch status{RESET}               — Status anzeigen\n")
                elif cmd[1].lower() == "stop":
                    print(_watcher.stop())
                elif cmd[1].lower() == "status":
                    print(_watcher.status())
                else:
                    watch_path = cmd[1]
                    watch_instr = " ".join(cmd[2:]) if len(cmd) > 2 else "Analysiere und kommentiere die Änderungen."
                    try:
                        result = _watcher.start(
                            path=watch_path,
                            instruction=watch_instr,
                            agent_callback=agent_loop,
                            thinking=thinking,
                            max_tokens=max_tokens,
                        )
                        print(result)
                    except Exception as e:
                        print(f"{RED}Watch konnte nicht gestartet werden: {e}{RESET}\n")

            # ── /reload ────────────────────────────────────────────────────
            elif cmd_lower == "/reload":
                import ast as _ast
                import glob as _glob
                pkg_dir = os.path.dirname(os.path.abspath(__file__))
                syntax_errors = []
                for py_file in sorted(_glob.glob(os.path.join(pkg_dir, "*.py"))):
                    try:
                        with open(py_file, "r", encoding="utf-8") as _f:
                            _ast.parse(_f.read())
                    except SyntaxError as _e:
                        syntax_errors.append(
                            f"  {RED}{os.path.basename(py_file)}{RESET}: Zeile {_e.lineno}: {_e.msg}"
                        )
                if syntax_errors:
                    print(f"\n{RED}Reload abgebrochen – Syntax-Fehler:{RESET}")
                    for _err in syntax_errors:
                        print(_err)
                    print(f"{DIM}Fehler beheben und /reload erneut versuchen.{RESET}\n")
                    continue
                print(f"{YELLOW}Lade Local CLI Agent neu...{RESET}")
                os.execv(sys.executable, [sys.executable, "-m", "local_cli_agent.cli"] + sys.argv[1:])

            # ── /version ───────────────────────────────────────────────────
            elif cmd_lower == "/version":
                print(f"{DIM}Local CLI Agent v{VERSION}{RESET}")
                print(f"{DIM}Modell:  {get_model_name() or 'keines'}{RESET}")
                print(f"{DIM}Quelle:  {SCRIPT_FILE}{RESET}")
                print()

            # ── /changelog ─────────────────────────────────────────────────
            elif cmd_lower == "/changelog":
                cl = get_changelog()
                print(f"{DIM}{cl}{RESET}\n")

            # ── /help ──────────────────────────────────────────────────────
            elif cmd_lower == "/help":
                print_banner()

            # ── Unbekannt ──────────────────────────────────────────────────
            else:
                print(f"{DIM}Unbekannter Befehl. /help für alle Befehle.{RESET}\n")

            continue

        # ── Auto-suggest orchestrator for complex tasks ───────────────────
        if _orchestrator.should_suggest(user_input):
            print(
                f"\n{BOLD}{YELLOW}[!]{RESET} Komplexe Aufgabe erkannt. "
                f"Soll der {BOLD}Orchestrator{RESET} verwendet werden?\n"
                f"    {DIM}Mehrere Spezialisten arbeiten nacheinander "
                f"(Architekt → Backend → Tester → Verifikation → ...){RESET}"
            )
            try:
                orch_choice = input(
                    f"    [{BOLD}Enter{RESET}] = Orchestrator  "
                    f"[{BOLD}n{RESET}] = Direkt machen  "
                ).strip().lower()
            except (EOFError, KeyboardInterrupt):
                orch_choice = "n"

            if orch_choice != "n":
                _orchestrator.run_orchestration(
                    goal=user_input,
                    messages=messages,
                    agent_callback=agent_loop,
                    thinking=thinking,
                    max_tokens=max_tokens,
                )
                print()
                continue

        # ── Send message to agent ─────────────────────────────────────────
        messages.append({"role": "user", "content": user_input})
        agent_loop(messages, thinking=thinking, max_tokens=max_tokens)
        print()


def oneshot_mode(prompt, thinking=True, system_prompt=None, max_tokens=16384):
    """Send a single prompt and print the response."""
    messages = [
        {"role": "system", "content": build_system_prompt(system_prompt)},
        {"role": "user", "content": prompt},
    ]
    agent_loop(messages, thinking=thinking, max_tokens=max_tokens)
    print()