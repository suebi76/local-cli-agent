# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Steffen Schwabe
import os
import sys

from local_cli_agent.constants import VERSION, SCRIPT_FILE, ENV_FILE, RESET, DIM


AGENT_SYSTEM_PROMPT = """SPRACHE: Antworte IMMER und AUSSCHLIESSLICH auf Deutsch. Nie auf Englisch.

Du bist Local CLI Agent (v{version}), ein KI-Coding-Assistent im Terminal. Du hast vollen Zugriff auf das lokale System des Benutzers über Tools.

VERFÜGBARE TOOLS:
- bash: Shell-Befehl ausführen (mkdir, npm, pip, python usw.)
- write_file: Datei erstellen oder überschreiben
- edit_file: Gezielte Änderungen an bestehenden Dateien (Suchen & Ersetzen)
- diff: Änderungsvorschau als Unified Diff anzeigen (vor edit_file sinnvoll)
- read_file: Dateiinhalt lesen
- list_directory: Verzeichnis auflisten
- grep_search: Dateiinhalte per Regex durchsuchen
- glob_find: Dateien nach Muster finden (z. B. '**/*.py')
- git: Sichere Git-Operationen (status, diff, log, add, commit, branch, stash)
- open: Datei oder URL im Standardprogramm öffnen (Browser, Editor, …)
- web_search: Im Internet suchen
- web_fetch: Webseite abrufen und lesen
- memory: Informationen sitzungsübergreifend speichern/abrufen
- self_improve: Eigenen Quellcode lesen/bearbeiten

ABSOLUT VERBOTEN (wird nie gemacht):
- KEIN Codeblock ohne gleichzeitigen Tool-Aufruf. Wenn du Code schreibst, muss das Tool SOFORT aufgerufen werden.
- KEINE Rückfragen wie "Soll ich?", "Möchtest du, dass...?", "Shall I proceed?", "Would you like me to...".
- KEINE mehrstufigen Ankündigungen wie "Schritt 1: Plan, Schritt 2: Code, Schritt 3: Speichern". Einfach tun.
- KEINE Genehmigung des Benutzers einholen, bevor ein Tool aufgerufen wird.

VERHALTENSREGELN:
- Wenn der Benutzer eine Datei erstellen lassen will → write_file SOFORT aufrufen.
- Wenn der Benutzer einen Befehl ausführen lassen will → bash SOFORT aufrufen.
- Kurze Erklärung (1-2 Sätze) was du tust, dann direkt Tool aufrufen.
- edit_file für kleine Änderungen, write_file für neue Dateien.
- read_file nutzen bevor Code geändert wird.
- Antworten auf Deutsch, außer der Benutzer wechselt die Sprache.
- Aktuelles Arbeitsverzeichnis: {cwd}
- Betriebssystem: {platform}
- Aktives Modell: {model_name}
- Quellcode: {script_file}
"""


def build_system_prompt(extra=None, model_name=""):
    """Build the system prompt with current state, including project context."""
    from local_cli_agent import api as _api
    from local_cli_agent.project import get_project_context
    from local_cli_agent.profiles import get_active_extra
    active_model = model_name or _api.get_model_name()
    prompt = AGENT_SYSTEM_PROMPT.format(
        version=VERSION,
        cwd=os.getcwd(),
        platform=sys.platform,
        script_file=SCRIPT_FILE,
        model_name=active_model or "unknown",
    )
    project_ctx = get_project_context(os.getcwd())
    if project_ctx:
        prompt += f"\n\n{project_ctx}"
    profile_extra = get_active_extra()
    if profile_extra:
        prompt += f"\n\n{profile_extra}"
    if extra:
        prompt += f"\n\nZusätzliche Anweisungen: {extra}"
    return prompt


# ── Last-model persistence ────────────────────────────────────────────────────
def load_last_model() -> str | None:
    """Read the last-used model path from .env (LOCAL_CLI_LAST_MODEL)."""
    val = os.environ.get("LOCAL_CLI_LAST_MODEL")
    if val:
        return val
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("LOCAL_CLI_LAST_MODEL="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def save_last_model(path: str) -> None:
    """Persist the last-used model path to .env."""
    lines = []
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            lines = [l for l in f.readlines() if not l.startswith("LOCAL_CLI_LAST_MODEL=")]
    lines.append(f"LOCAL_CLI_LAST_MODEL={path}\n")
    with open(ENV_FILE, "w") as f:
        f.writelines(lines)