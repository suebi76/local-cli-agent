# Local CLI Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-2.0.0-brightgreen.svg)](CHANGELOG.md)

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
- **Full tool use** — bash, file read/write/edit, grep, glob, web search & fetch
- **Persistent memory** — remembers project context and preferences across sessions
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
local-cli                                          # Interactive chat
local-cli "Create a Flask API with JWT auth"       # One-shot
local-cli -s "You are a senior Rust developer"     # Custom system prompt
local-cli --max-tokens 8192                        # Set token limit
```

**Example session**
```
==================================================================
  Local CLI Agent v2.0.0
  Self-improving AI coding assistant
  Model: qwen2.5-coder:7b
==================================================================

You: Create a responsive landing page for my SaaS "DataSync"

  ⠋ Generating...

  [2 tool call(s)]
  [auto] write_file: index.html
  [auto] write_file: style.css

Done. Open index.html in your browser to preview.

You: /save
Saved: session_20260405_143022.md
```

### Slash Commands

| Command | Description |
|---|---|
| `/auto [on\|off]` | Toggle auto-approval for tool execution |
| `/clear` | Clear conversation history |
| `/cd <path>` | Change working directory |
| `/compact` | Summarize conversation to save tokens |
| `/model` | Switch model without restarting |
| `/save` | Export conversation as Markdown |
| `/memory` | Show all saved memories |
| `/history` | Show message history |
| `/tokens <n>` | Set max output tokens (e.g. `/tokens 8192`) |
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
| `read_file` | Read file contents |
| `list_directory` | List files and directories |
| `grep_search` | Search file contents with regex |
| `glob_find` | Find files by pattern |
| `web_search` | Search the internet (DuckDuckGo) |
| `web_fetch` | Fetch and read web pages |
| `memory` | Persistent key-value memory across sessions |
| `self_improve` | Read/edit own source, create backups, view changelog |

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
- **Vollständiges Tool-System** — bash, Dateien lesen/schreiben/bearbeiten, grep, glob, Websuche
- **Persistentes Gedächtnis** — merkt sich Projektkontext und Einstellungen über Sitzungen hinweg
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
local-cli                                            # Interaktiver Chat
local-cli "Erstelle eine Flask-API mit JWT-Auth"     # Einmalige Anfrage
local-cli -s "Du bist ein erfahrener Rust-Entwickler" # Eigener System-Prompt
local-cli --max-tokens 8192                          # Token-Limit setzen
```

### Slash-Befehle

| Befehl | Beschreibung |
|---|---|
| `/auto [on\|off]` | Tool-Ausführung auto-bestätigen |
| `/clear` | Konversationsverlauf löschen |
| `/cd <pfad>` | Arbeitsverzeichnis wechseln |
| `/compact` | Konversation komprimieren (spart Tokens) |
| `/model` | Modell wechseln ohne Neustart |
| `/save` | Konversation als Markdown speichern |
| `/memory` | Gespeicherte Erinnerungen anzeigen |
| `/history` | Nachrichtenverlauf anzeigen |
| `/tokens <n>` | Max. Output-Tokens setzen (z.B. `/tokens 8192`) |
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
| `read_file` | Dateiinhalt lesen |
| `list_directory` | Verzeichnis auflisten |
| `grep_search` | Dateiinhalt mit Regex durchsuchen |
| `glob_find` | Dateien nach Muster suchen |
| `web_search` | Im Internet suchen (DuckDuckGo) |
| `web_fetch` | Webseiten laden und lesen |
| `memory` | Persistentes Schlüssel-Wert-Gedächtnis |
| `self_improve` | Quellcode lesen/bearbeiten, Backup, Changelog |

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
