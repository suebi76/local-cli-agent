# Local CLI Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-2.3.0-brightgreen.svg)](CHANGELOG.md)

[🇬🇧 English](#english) · [🇩🇪 Deutsch](#deutsch)

---

<a name="english"></a>
## 🇬🇧 English

> A self-improving AI coding assistant that runs entirely on your local machine —
> no cloud, no API key, no data leaving your computer.

Local CLI Agent connects to [Ollama](https://ollama.com) or [LM Studio](https://lmstudio.ai),
giving you a powerful terminal agent that can write code, edit files, run commands, search
the web, and even improve its own source code.

### Features

- **Runs 100% locally** — Ollama or LM Studio as backend, no cloud required
- **Full tool use** — bash, file read/write/edit, diff, git, grep, glob, web search & fetch
- **Agent profiles** — 14 built-in personas: Vibe-Coder, Refactor, Reviewer, Debugger, Explainer, Frontend, Backend, Tester, Security, Docs, Performance, Architect, DevOps
- **Mission mode** — give a high-level goal; agent plans it, executes step by step, pauses for review
- **Auto-test loop** — runs your test suite after every file change; agent self-corrects on failure
- **Undo system** — every file change is snapshotted; `/undo` restores any previous state instantly
- **Project memory** — auto-detects your project (Python, Node, Rust, Go…) and injects context into every prompt
- **Watch mode** — monitors a path and triggers the agent automatically on every file change
- **Persistent memory** — remembers facts and preferences across sessions
- **Self-improvement** — the agent can read and edit its own source code (with backup & syntax check)
- **Conversation export** — save any session as Markdown with `/save`
- **Token-efficient** — compress long conversations with `/compact`
- **Auto-approve mode** — run without confirmation prompts for trusted workflows
- **Model switching** — switch models mid-session with `/model`
- **Reasoning model support** — filters `<|think|>` blocks, falls back to markdown extraction for models without native tool-calling

### Requirements

- **Python 3.10+**
- **[Ollama](https://ollama.com)** (recommended) — free, runs as a background service
  _or_
- **[LM Studio](https://lmstudio.ai)** — GUI app with integrated model browser

No API key. No account. No internet connection required during chat.

### Quick Start

**Windows**
```
1. Download or clone this repository
2. Double-click install.bat
3. Open a new terminal and run: local-cli
```

**macOS / Linux**
```bash
git clone https://github.com/suebi76/local-cli-agent.git
cd local-cli-agent
chmod +x install.sh && ./install.sh
```

**Install a model (Ollama)**
```bash
ollama pull llama3.2          # 2 GB  — fast, general purpose
ollama pull qwen2.5-coder     # 4.7 GB — best for coding tasks
ollama pull gemma3:12b        # 8 GB  — strong general model
```

**Install a model (LM Studio)**
1. Open LM Studio → search for a model → download
2. Go to **Developer** tab → select the model → **Start Server**
3. Run `local-cli` — the loaded model is detected automatically

### Usage

```bash
local-cli                                              # Interactive chat
local-cli "Create a Flask API with JWT auth"           # One-shot
local-cli -s "You are a senior Rust developer"         # Custom system prompt
local-cli --watch ./src "run tests on every change"    # Watch mode
```

**Example session**
```
==================================================================
  Local CLI Agent v2.1.0
  Self-improving AI coding assistant
  Model: qwen2.5-coder:7b
==================================================================

You: Create a responsive landing page for my SaaS "DataSync"

  [2 tool call(s)]
  [auto] write_file: index.html
  [auto] write_file: style.css

Done. Open index.html in your browser to preview.

You: /undo
Restored: index.html, style.css  (checkpoint: write_file)

You: /watch ./src "Run tests and show what broke"
Watch started: ./src
Interval: 2s  |  /watch stop to exit
```

### Slash Commands

| Command | Description |
|---|---|
| `/auto [on\|off]` | Toggle auto-approval for tool execution |
| `/clear` | Clear conversation history |
| `/cd <path>` | Change working directory |
| `/compact` | Summarize conversation to save tokens |
| `/profile` | Switch agent profile (shows selector) |
| `/profile <id>` | Activate profile directly (e.g. `/profile aufraumen`) |
| `/model` | Switch model without restarting |
| `/save` | Export conversation as Markdown |
| `/memory` | Show all saved memories |
| `/history` | Show message history |
| `/tokens <n>` | Set max output tokens (e.g. `/tokens 8192`) |
| `/undo [n]` | Undo the last n file changes |
| `/checkpoint [name]` | Set a manual restore point |
| `/mission <goal>` | Start mission mode (plan + execute) |
| `/autotest <cmd>` | Auto-run tests after every file change |
| `/autotest off` | Disable auto-test |
| `/watch <path> <instruction>` | Start watch mode |
| `/watch stop` | Stop watch mode |
| `/watch status` | Show watch mode status |
| `/reload` | Reload after self-improvement |
| `/version` | Show version and model info |
| `/changelog` | Show self-improvement history |
| `/help` | Show help |
| `/quit` | Exit (or Ctrl+C) |

### Built-in Tools

| Tool | Description |
|---|---|
| `bash` | Execute shell commands |
| `write_file` | Create or overwrite files |
| `edit_file` | Targeted find & replace in files |
| `diff` | Preview changes as unified diff before editing |
| `read_file` | Read file contents |
| `list_directory` | List files and directories |
| `grep_search` | Search file contents with regex |
| `glob_find` | Find files by pattern |
| `git` | Safe git operations (status, diff, log, add, commit, branch, stash) |
| `open` | Open a file or URL in the default application |
| `web_search` | Search the internet (DuckDuckGo) |
| `web_fetch` | Fetch and read web pages |
| `memory` | Persistent key-value memory across sessions |
| `self_improve` | Read/edit own source, create backups, view changelog |

### Agent Profiles

Switch the agent's personality to match your current task. No technical knowledge required —
just pick from the list and the agent adapts its entire behavior.

```
/profile              → opens the selector
/profile aufraumen    → activate directly by ID
/profile off          → back to standard
```

| ID | Profile | Best for |
|---|---|---|
| `standard` | 🤖 Standard | General-purpose assistant |
| `vibe` | ⚡ Vibe-Coder | Just make it work — fast, pragmatic, no lectures |
| `aufraumen` | 🏗️ Refactor & Restructure | Split large files into clean logical modules |
| `reviewer` | 🔍 Code Reviewer | Structured feedback — never writes code, only analyses |
| `debugger` | 🐛 Bug Hunter | Methodical bug finding and fixing |
| `erklarer` | 📖 Explainer | Everything in plain language, no jargon |
| `frontend` | 🎨 Frontend | HTML, CSS, JS — beautiful, accessible, responsive |
| `backend` | ⚙️ Backend | APIs, databases, servers, security |
| `tester` | 🧪 Tester | Tests that actually catch bugs |
| `security` | 🛡️ Security | Find vulnerabilities before someone else does |
| `docs` | 📝 Documentation | README, comments, API docs people actually read |
| `performance` | 🚀 Performance | Find bottlenecks, measure, then optimize |
| `architect` | 🏛️ Architect | Plan structure before writing a single line |
| `devops` | 🐳 DevOps | Docker, CI/CD, deployment, infrastructure |

**The Refactor profile in action:**

```
/profile aufraumen

You: Diese Datei hat 800 Zeilen, bitte aufteilen: /app.py

→ Agent liest app.py
→ Erstellt Plan: models.py, routes.py, auth.py, utils.py, config.py
→ Teilt auf, korrigiert alle Imports
→ Führt Tests aus
→ Zusammenfassung was wohin verschoben wurde
```

### Mission Mode

Give the agent a high-level goal. It creates a numbered plan, asks for your confirmation,
and executes each step one by one — pausing between steps so you stay in control.
The complete conversation history grows naturally: later steps have full context of earlier ones.

```bash
# From the CLI (no interactive session needed)
local-cli --mission "Add JWT authentication to the Flask API"

# Inside an interactive session
/mission Refactor all database queries to use async/await
```

```
Mission: Add JWT authentication to the Flask API
────────────────────────────────────────────────────────────
   1/5  Analyse current auth.py and routes.py
   2/5  Install PyJWT dependency and update requirements.txt
   3/5  Implement token generation in auth.py
   4/5  Add JWT middleware to protected routes
   5/5  Write tests for login and token validation
────────────────────────────────────────────────────────────

Mission starten? [Enter] = ja  [n] = abbrechen
```

After each step: **Enter** to continue · **s** to stop.

### Auto-Test Loop

Enable once, forget about it. After every `write_file` or `edit_file`, the agent
automatically runs your test suite and sees the result — no human in the loop required.

```
/autotest pytest tests/ -x        # enable (any shell command works)
/autotest npm test                 # works with any test runner
/autotest off                      # disable
```

**What happens on failure:**
The test output is appended directly to the tool result the agent receives.
It sees the failure immediately, diagnoses the cause, and writes a fix — all in the
same agent loop iteration, without you doing anything.

```
[auto] write_file: auth.py

[autotest] FAILED
  FAILED tests/test_auth.py::test_login - AssertionError: 401 != 200
  1 failed in 0.43s

→ Agent sees failure, corrects auth.py, tests run again → PASSED ✓
```

### Undo System

Every `write_file` and `edit_file` call automatically saves a snapshot of the affected file.
Restore previous states at any time — no git commit required.

```
You: Refactor auth.py completely

  [tool] write_file: auth.py  ✓

You: /undo
Restored: auth.py  (checkpoint: write_file: auth.py)

You: /checkpoint before-big-refactor
Checkpoint set: before-big-refactor

You: /undo 3      # undo the last 3 changes
Restored 3 checkpoints.
```

### Project Memory (Auto-Context)

On every prompt, Local CLI Agent scans your working directory and injects a project summary
into the system prompt — silently, without you having to explain anything.

**Detected automatically:**
- Language / stack: Python, Node.js, Rust, Go, Java, .NET, Flutter, PHP, Ruby
- Project name, version, description (from `pyproject.toml`, `package.json`, `Cargo.toml`, …)
- Dependencies (first 8 entries)
- Test framework (pytest, Jest, Vitest, …)
- Git branch + last commit message
- README summary (first meaningful line)

```
--- PROJECT CONTEXT ---
Project: local-cli-agent v2.1.0
Description: Self-improving AI coding assistant with full tool use
Stack: Python
Dependencies: requests, prompt_toolkit
Test framework: pytest
Git branch: main  |  Last commit: feat: add watch mode
--- END PROJECT CONTEXT ---
```

Results are cached using an mtime fingerprint — no performance overhead.

### Watch Mode

Monitors a directory or file and triggers the agent automatically whenever something changes.
Ideal for AI-assisted TDD, live code review, or automated documentation updates.

```bash
# Start from the CLI
local-cli --watch ./src "Run the tests and fix what fails"

# Start from inside an interactive session
/watch ./src "Run the tests and fix what fails"
/watch stop
/watch status
```

- Polls every 2 seconds using `os.stat()` — no extra dependencies
- Skips `.git`, `node_modules`, `__pycache__`, `.venv`, `dist`, `build`
- Reports which files changed before triggering the agent
- Runs in a background thread — the interactive session stays usable

### Self-Improvement

Local CLI Agent can modify its own source code. Ask it directly:

```
"Add a /stats command that shows token usage per message"
"Read your executor.py and suggest optimizations"
"Improve the error handling in the bash tool"
```

**Safety guarantees:**
- Every edit requires a backup first — aborts if backup fails
- Python syntax is validated before any `.py` file is written
- `/reload` validates all package files before restarting

### Configuration

Settings are stored in `~/.local-cli-agent/.env`:

```env
LOCAL_CLI_OLLAMA_URL=http://localhost:11434
LOCAL_CLI_LMSTUDIO_URL=http://localhost:1234
```

### Model Backends

| Backend | Default URL | Notes |
|---|---|---|
| Ollama | `localhost:11434` | Runs as a system service |
| LM Studio | `localhost:1234` | Server must be started manually |

**Recommended models:**

| Model | Size | Strength |
|---|---|---|
| `qwen2.5-coder:7b` | 4.7 GB | Best tool-calling and coding |
| `llama3.2:3b` | 2.0 GB | Fast, reliable, general purpose |
| `gemma3:12b` | 8.0 GB | Strong reasoning |
| `mistral:7b` | 4.1 GB | Good instruction following |

### Development

```bash
git clone https://github.com/suebi76/local-cli-agent.git
cd local-cli-agent
pip install -e ".[dev]"
pytest tests/ -v
ruff check local_cli_agent/
```

### Uninstall

**Windows:** Double-click `uninstall.bat`
**macOS / Linux:** `chmod +x uninstall.sh && ./uninstall.sh`

### Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Bug reports and feature requests via
[GitHub Issues](https://github.com/suebi76/local-cli-agent/issues).

### License

[MIT License](LICENSE) — Copyright (c) 2026 Steffen Schwabe

---

<a name="deutsch"></a>
## 🇩🇪 Deutsch

> Ein selbstverbessernder KI-Coding-Assistent, der vollständig auf deinem lokalen Rechner läuft —
> keine Cloud, kein API-Key, keine Daten verlassen deinen Computer.

Local CLI Agent verbindet sich mit [Ollama](https://ollama.com) oder [LM Studio](https://lmstudio.ai)
und bietet einen leistungsstarken Terminal-Agenten, der Code schreiben, Dateien bearbeiten,
Befehle ausführen, im Web suchen und sogar seinen eigenen Quellcode verbessern kann.

### Funktionen

- **100% lokal** — Ollama oder LM Studio als Backend, keine Cloud erforderlich
- **Vollständiges Tool-System** — bash, Dateien lesen/schreiben/bearbeiten, diff, git, grep, glob, Websuche
- **Agent-Profile** — 14 eingebaute Persönlichkeiten: Vibe-Coder, Aufräumen, Reviewer, Debugger, Erklärer, Frontend, Backend, Tester, Sicherheit, Docs, Performance, Architekt, DevOps
- **Mission-Mode** — gib ein übergeordnetes Ziel vor; Agent plant und führt es schrittweise aus
- **Auto-Test-Loop** — führt nach jeder Dateiänderung automatisch deine Tests aus; Agent korrigiert sich selbst
- **Undo-System** — jede Dateiänderung wird gespeichert; `/undo` stellt jeden vorherigen Zustand sofort wieder her
- **Projekt-Memory** — erkennt automatisch dein Projekt (Python, Node, Rust, Go…) und injiziert den Kontext in jeden Prompt
- **Watch-Mode** — beobachtet einen Pfad und löst den Agenten bei jeder Dateiänderung automatisch aus
- **Persistentes Gedächtnis** — merkt sich Fakten und Einstellungen über Sitzungen hinweg
- **Selbstverbesserung** — der Agent kann seinen eigenen Quellcode lesen und bearbeiten (mit Backup & Syntax-Check)
- **Konversations-Export** — Sitzung mit `/save` als Markdown speichern
- **Token-effizient** — lange Gespräche mit `/compact` komprimieren
- **Auto-Bestätigung** — Werkzeuge ohne Rückfrage ausführen mit `/auto on`
- **Modellwechsel** — Modell während der Sitzung wechseln mit `/model`
- **Reasoning-Modell-Unterstützung** — filtert `<|think|>`-Blöcke, Markdown-Fallback für Modelle ohne nativen Tool-Call

### Voraussetzungen

- **Python 3.10+**
- **[Ollama](https://ollama.com)** (empfohlen) — kostenlos, läuft als Hintergrunddienst
  _oder_
- **[LM Studio](https://lmstudio.ai)** — GUI-App mit integriertem Modell-Browser

Kein API-Key. Kein Account. Keine Internetverbindung während des Chats erforderlich.

### Schnellstart

**Windows**
```
1. Repository herunterladen oder klonen
2. install.bat doppelklicken
3. Neues Terminal öffnen und eingeben: local-cli
```

**macOS / Linux**
```bash
git clone https://github.com/suebi76/local-cli-agent.git
cd local-cli-agent
chmod +x install.sh && ./install.sh
```

**Modell installieren (Ollama)**
```bash
ollama pull llama3.2          # 2 GB  — schnell, allgemein
ollama pull qwen2.5-coder     # 4.7 GB — beste Code-Performance
ollama pull gemma3:12b        # 8 GB  — starkes Allgemeinmodell
```

**Modell installieren (LM Studio)**
1. LM Studio öffnen → Modell suchen → herunterladen
2. Tab **Developer** → Modell auswählen und laden → **Start Server**
3. `local-cli` starten — das geladene Modell wird automatisch erkannt

### Benutzung

```bash
local-cli                                                         # Interaktiver Chat
local-cli "Erstelle eine Flask-API mit JWT-Auth"                  # Einmalige Anfrage
local-cli -s "Du bist ein erfahrener Rust-Entwickler"             # Eigener System-Prompt
local-cli --watch ./src "Führe Tests bei jeder Änderung aus"      # Watch-Mode
```

### Slash-Befehle

| Befehl | Beschreibung |
|---|---|
| `/auto [on\|off]` | Tool-Ausführung auto-bestätigen |
| `/clear` | Konversationsverlauf löschen |
| `/cd <pfad>` | Arbeitsverzeichnis wechseln |
| `/compact` | Konversation komprimieren (spart Tokens) |
| `/profile` | Agenten-Profil wechseln (Auswahl-Menü) |
| `/profile <id>` | Profil direkt aktivieren (z.B. `/profile aufraumen`) |
| `/model` | Modell wechseln ohne Neustart |
| `/save` | Konversation als Markdown speichern |
| `/memory` | Gespeicherte Erinnerungen anzeigen |
| `/history` | Nachrichtenverlauf anzeigen |
| `/tokens <n>` | Max. Output-Tokens setzen (z.B. `/tokens 8192`) |
| `/undo [n]` | Letzte n Dateiänderungen rückgängig machen |
| `/checkpoint [name]` | Manuellen Rückgabepunkt setzen |
| `/mission <ziel>` | Mission-Mode starten (Agent plant + führt aus) |
| `/autotest <cmd>` | Tests nach jeder Änderung automatisch ausführen |
| `/autotest off` | Auto-Test deaktivieren |
| `/watch <pfad> <anweisung>` | Watch-Mode starten |
| `/watch stop` | Watch-Mode beenden |
| `/watch status` | Watch-Status anzeigen |
| `/reload` | Nach Self-Improvement neu laden |
| `/version` | Version und Modell-Info anzeigen |
| `/changelog` | Self-Improvement-Verlauf anzeigen |
| `/help` | Hilfe anzeigen |
| `/quit` | Beenden (oder Ctrl+C) |

### Werkzeuge

| Tool | Beschreibung |
|---|---|
| `bash` | Shell-Befehle ausführen |
| `write_file` | Dateien erstellen oder überschreiben |
| `edit_file` | Gezieltes Suchen & Ersetzen in Dateien |
| `diff` | Änderungsvorschau als Unified Diff (vor edit_file) |
| `read_file` | Dateiinhalt lesen |
| `list_directory` | Verzeichnis auflisten |
| `grep_search` | Dateiinhalt mit Regex durchsuchen |
| `glob_find` | Dateien nach Muster suchen |
| `git` | Sichere Git-Operationen (status, diff, log, add, commit, branch, stash) |
| `open` | Datei oder URL im Standardprogramm öffnen |
| `web_search` | Im Internet suchen (DuckDuckGo) |
| `web_fetch` | Webseiten laden und lesen |
| `memory` | Persistentes Schlüssel-Wert-Gedächtnis |
| `self_improve` | Quellcode lesen/bearbeiten, Backup, Changelog |

### Agent-Profile

Wechsle die Persönlichkeit des Agenten je nach Aufgabe. Kein technisches Vorwissen nötig —
einfach auswählen und der Agent passt sein gesamtes Verhalten an.

```
/profile              → Auswahl-Menü öffnen
/profile aufraumen    → Direkt per ID aktivieren
/profile off          → Zurück zum Standard
```

| ID | Profil | Am besten für |
|---|---|---|
| `standard` | 🤖 Standard | Allzweck-Assistent |
| `vibe` | ⚡ Vibe-Coder | Einfach machen — schnell, pragmatisch, kein Gerede |
| `aufraumen` | 🏗️ Aufräumen & Strukturieren | Große Dateien in saubere Module aufteilen |
| `reviewer` | 🔍 Code-Reviewer | Strukturiertes Feedback — schreibt nie Code, analysiert nur |
| `debugger` | 🐛 Fehlersuche | Methodisches Bugs-Finden und Beheben |
| `erklarer` | 📖 Erklärer | Alles in einfacher Sprache, kein Jargon |
| `frontend` | 🎨 Frontend | HTML, CSS, JS — schön, zugänglich, responsiv |
| `backend` | ⚙️ Backend | APIs, Datenbanken, Server, Sicherheit |
| `tester` | 🧪 Tester | Tests die wirklich Bugs fangen |
| `security` | 🛡️ Sicherheit | Schwachstellen finden bevor jemand anderes es tut |
| `docs` | 📝 Dokumentation | README, Kommentare, API-Docs die gelesen werden |
| `performance` | 🚀 Performance | Engpässe finden, messen, dann optimieren |
| `architect` | 🏛️ Architekt | Erst planen, dann eine einzige Zeile schreiben |
| `devops` | 🐳 DevOps | Docker, CI/CD, Deployment, Infrastruktur |

**Das Aufräumen-Profil in der Praxis:**

```
/profile aufraumen

Du: Diese Datei hat 800 Zeilen, bitte aufteilen: /app.py

→ Agent liest app.py vollständig
→ Erstellt Plan: models.py, routes.py, auth.py, utils.py, config.py
→ Teilt auf, korrigiert alle Import-Zeilen
→ Führt Tests aus
→ Zusammenfassung: was wurde wohin verschoben
```

### Mission-Mode

Gib dem Agenten ein übergeordnetes Ziel. Er erstellt einen nummerierten Plan, fragt dich
um Bestätigung und führt jeden Schritt einzeln aus — mit Pause zwischen den Schritten,
damit du jederzeit eingreifen kannst.

```bash
# Beim Start per CLI
local-cli --mission "JWT-Authentifizierung zur Flask-API hinzufügen"

# In einer laufenden Sitzung
/mission Alle Datenbankabfragen auf async/await umstellen
```

```
Mission: JWT-Authentifizierung zur Flask-API hinzufügen
────────────────────────────────────────────────────────────
   1/5  Aktuelle auth.py und routes.py analysieren
   2/5  PyJWT installieren und requirements.txt aktualisieren
   3/5  Token-Generierung in auth.py implementieren
   4/5  JWT-Middleware zu geschützten Routen hinzufügen
   5/5  Tests für Login und Token-Validierung schreiben
────────────────────────────────────────────────────────────

Mission starten? [Enter] = ja  [n] = abbrechen
```

Nach jedem Schritt: **Enter** = weiter · **s** = stopp.

### Auto-Test-Loop

Einmal aktivieren, den Rest erledigt der Agent. Nach jedem `write_file` oder `edit_file`
läuft die Testsuite automatisch — kein manuelles Eingreifen nötig.

```
/autotest pytest tests/ -x        # aktivieren (beliebiger Shell-Befehl)
/autotest npm test                 # funktioniert mit jedem Test-Runner
/autotest off                      # deaktivieren
```

**Was bei Fehlern passiert:**
Die Testausgabe wird direkt ans Tool-Ergebnis angehängt, das der Agent sieht.
Er erkennt den Fehler sofort, analysiert die Ursache und schreibt eine Korrektur —
alles in derselben Agent-Loop-Iteration, ohne dass du etwas tun musst.

### Undo-System

Jeder `write_file`- und `edit_file`-Aufruf speichert automatisch einen Snapshot der betroffenen Datei.
Vorherige Zustände können jederzeit wiederhergestellt werden — ganz ohne Git-Commit.

```
Du: Refaktoriere auth.py komplett

  [tool] write_file: auth.py  ✓

Du: /undo
Wiederhergestellt: auth.py  (Checkpoint: write_file: auth.py)

Du: /checkpoint vor-grossem-refactor
Checkpoint gesetzt: vor-grossem-refactor

Du: /undo 3      # letzte 3 Änderungen rückgängig machen
3 Checkpoints wiederhergestellt.
```

### Projekt-Memory (Auto-Kontext)

Bei jedem Prompt scannt Local CLI Agent das Arbeitsverzeichnis und injiziert eine Projektzusammenfassung
in den System-Prompt — ohne dass du etwas erklären musst.

**Wird automatisch erkannt:**
- Sprache / Stack: Python, Node.js, Rust, Go, Java, .NET, Flutter, PHP, Ruby
- Projektname, Version, Beschreibung (aus `pyproject.toml`, `package.json`, `Cargo.toml`, …)
- Abhängigkeiten (erste 8 Einträge)
- Test-Framework (pytest, Jest, Vitest, …)
- Git-Branch + letzter Commit
- README-Zusammenfassung (erste aussagekräftige Zeile)

Ergebnisse werden per mtime-Fingerprint gecacht — kein Performance-Overhead.

### Watch-Mode

Beobachtet ein Verzeichnis oder eine Datei und löst den Agenten automatisch bei jeder Änderung aus.
Ideal für KI-gestütztes TDD, Live-Code-Review oder automatische Dokumentations-Updates.

```bash
# Beim Start per CLI
local-cli --watch ./src "Führe Tests aus und behebe Fehler"

# In einer laufenden Sitzung
/watch ./src "Führe Tests aus und behebe Fehler"
/watch stop
/watch status
```

- Pollt alle 2 Sekunden via `os.stat()` — keine zusätzlichen Abhängigkeiten
- Überspringt `.git`, `node_modules`, `__pycache__`, `.venv`, `dist`, `build`
- Zeigt an, welche Dateien sich geändert haben
- Läuft im Hintergrund-Thread — die interaktive Sitzung bleibt nutzbar

### Selbstverbesserung

Local CLI Agent kann seinen eigenen Quellcode ändern. Einfach direkt fragen:

```
"Füge einen /stats-Befehl hinzu, der die Token-Nutzung anzeigt"
"Lies deine executor.py und schlage Verbesserungen vor"
"Verbessere die Fehlermeldung wenn ein Tool fehlschlägt"
```

**Sicherheitsgarantien:**
- Jede Änderung erfordert zuerst ein Backup — Abbruch wenn Backup fehlschlägt
- Python-Syntax wird vor jedem Schreiben einer `.py`-Datei validiert
- `/reload` prüft alle Paketdateien auf Syntax-Fehler vor dem Neustart

### Konfiguration

Einstellungen werden in `~/.local-cli-agent/.env` gespeichert:

```env
LOCAL_CLI_OLLAMA_URL=http://localhost:11434
LOCAL_CLI_LMSTUDIO_URL=http://localhost:1234
```

### Empfohlene Modelle

| Modell | Größe | Stärke |
|---|---|---|
| `qwen2.5-coder:7b` | 4,7 GB | Beste Tool-Nutzung und Code |
| `llama3.2:3b` | 2,0 GB | Schnell, zuverlässig, allgemein |
| `gemma3:12b` | 8,0 GB | Starkes Reasoning |
| `mistral:7b` | 4,1 GB | Gute Instruction-Following |

### Deinstallation

**Windows:** `uninstall.bat` doppelklicken
**macOS / Linux:** `chmod +x uninstall.sh && ./uninstall.sh`

### Beitragen

Siehe [CONTRIBUTING.md](CONTRIBUTING.md). Fehlerberichte und Feature-Wünsche über
[GitHub Issues](https://github.com/suebi76/local-cli-agent/issues).

### Lizenz

[MIT-Lizenz](LICENSE) — Copyright (c) 2026 Steffen Schwabe
