# Local CLI Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-2.0.0-brightgreen.svg)](CHANGELOG.md)

> A self-improving AI coding assistant that runs entirely on your local machine —
> no cloud, no API key, no data leaving your computer.

Local CLI Agent connects to [Ollama](https://ollama.com) or [LM Studio](https://lmstudio.ai),
giving you a powerful terminal agent that can write code, edit files, run commands, search
the web, and even improve its own source code.

---

## Features

- **Runs 100% locally** — Ollama or LM Studio as backend, no cloud required
- **Full tool use** — bash, file read/write/edit, grep, glob, web search & fetch
- **Persistent memory** — remembers project context and preferences across sessions
- **Self-improvement** — the agent can read and edit its own source code (with backup & syntax check)
- **Conversation export** — save any session as Markdown with `/save`
- **Token-efficient** — compress long conversations with `/compact`
- **Auto-approve mode** — run without confirmation prompts for trusted workflows
- **Model switching** — switch models mid-session with `/model`
- **Reasoning model support** — filters `<|think|>` blocks, falls back to markdown extraction for models without native tool-calling

---

## Requirements

- **Python 3.10+**
- **[Ollama](https://ollama.com)** (recommended) — free, runs as a background service
  _or_
- **[LM Studio](https://lmstudio.ai)** — GUI app with integrated model browser

No API key. No account. No internet connection required during chat.

---

## Quick Start

### Windows

```
1. Download or clone this repository
2. Double-click install.bat
3. Open a new terminal and run: local-cli
```

The installer handles Python, pip, PATH, and guides you through setting up a model backend.

### macOS / Linux

```bash
git clone https://github.com/suebi76/local-cli-agent.git
cd local-cli-agent
chmod +x install.sh && ./install.sh
```

### Install a model (Ollama)

```bash
ollama pull llama3.2          # 2 GB  — fast, general purpose
ollama pull qwen2.5-coder     # 4.7 GB — best for coding tasks
ollama pull gemma3:12b        # 8 GB  — strong general model
```

### Install a model (LM Studio)

1. Open LM Studio → search for a model → download
2. Go to **Developer** tab → select the model → **Start Server**
3. Run `local-cli` — the loaded model is detected automatically

---

## Usage

```bash
# Interactive chat (default)
local-cli

# One-shot command
local-cli "Create a Python Flask API with JWT authentication"

# With custom system prompt
local-cli -s "You are a senior Rust developer"

# Set max output tokens
local-cli --max-tokens 8192
```

### Example session

```
==================================================================
  Local CLI Agent v2.0.0
  Self-improving AI coding assistant
  Modell: qwen2.5-coder:7b
==================================================================

You: Create a responsive landing page for my SaaS product "DataSync"

  ⠋ Generiere...

  [2 tool call(s)]
  [auto] write_file: index.html
  [auto] write_file: style.css

Created index.html and style.css — open index.html in your browser to preview.

You: /save
Gespeichert: session_20260405_143022.md
```

---

## Slash Commands

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

---

## Built-in Tools

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

---

## Self-Improvement

Local CLI Agent can modify its own source code. Ask it directly:

```
"Add a /stats command that shows token usage per message"
"Improve the error message when a tool fails"
"Read your executor.py and suggest optimizations"
```

**Safety guarantees:**
- Every edit requires a backup first — abort if backup fails
- Python syntax is validated before any `.py` file is written
- `/reload` validates all package files before restarting the process

---

## Configuration

Settings are read from `~/.local-cli-agent/.env` (global install) or `.env` in the
project root (development install):

```env
# Backend URLs — change only if using non-standard ports
LOCAL_CLI_OLLAMA_URL=http://localhost:11434
LOCAL_CLI_LMSTUDIO_URL=http://localhost:1234
```

All other state (memory, changelog, last used model) is also stored in `~/.local-cli-agent/`.

---

## Model Backends

| Backend | Default URL | Notes |
|---|---|---|
| Ollama | `localhost:11434` | Runs as a system service, always available |
| LM Studio | `localhost:1234` | Server must be started manually in the app |

Both can run simultaneously. When multiple models are available, an interactive
selector appears. When exactly one model is loaded, it is selected automatically.

**Recommended models for agent tasks:**

| Model | Size | Strength |
|---|---|---|
| `qwen2.5-coder:7b` | 4.7 GB | Best tool-calling and coding |
| `llama3.2:3b` | 2.0 GB | Fast, reliable, general purpose |
| `gemma3:12b` | 8.0 GB | Strong reasoning |
| `mistral:7b` | 4.1 GB | Good instruction following |

> **Note:** Models labeled "reasoning" or "thinking" (e.g. QwQ, DeepSeek-R1) have
> limited tool-calling capability. The agent detects this automatically and handles
> it gracefully via markdown extraction fallback.

---

## Development

```bash
# Clone and install in editable mode
git clone https://github.com/suebi76/local-cli-agent.git
cd local-cli-agent
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Lint
ruff check local_cli_agent/
```

---

## Uninstall

**Windows:** Double-click `uninstall.bat`

**macOS / Linux:**
```bash
chmod +x uninstall.sh && ./uninstall.sh
```

The uninstaller removes the package and optionally cleans up user data in
`~/.local-cli-agent/`. Ollama and LM Studio are **not** affected.

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting.

- **Bug reports** → [Open an issue](https://github.com/suebi76/local-cli-agent/issues/new?template=bug_report.md)
- **Feature requests** → [Open an issue](https://github.com/suebi76/local-cli-agent/issues/new?template=feature_request.md)
- **Pull requests** → Fork → feature branch → PR against `main`

---

## License

[MIT License](LICENSE) — Copyright (c) 2026 Steffen Schwabe
