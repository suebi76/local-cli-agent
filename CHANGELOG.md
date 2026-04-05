# Changelog

All notable changes to Local CLI Agent are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [2.4.0] — 2026-04-05

### Added
- **Master-Orchestrator** (`orchestrator.py`) — for complex tasks, a master LLM call produces
  a specialist plan (up to 10 steps, each assigned to the best profile). User can confirm,
  edit or abort before execution. Context summaries pass between steps.
  Available as `/orchestrate <goal>` and `local-cli --orchestrate "goal"`.
- **Auto-suggest** — when a prompt is detected as complex (heuristic score ≥ 0.55 based on
  word count + keywords), the system offers the orchestrator before sending to the agent.
  User can always decline with `n`.
- **Verification profile** (`verifikation`) — automatically inserted as penultimate step in
  every orchestration that contains code steps. Runs tests, checks imports, checks syntax,
  outputs structured ✅/❌ report, fixes errors immediately.
- **Interactive plan editor** — before orchestration starts, `[e]` opens an editor where
  the user can add, remove, or modify steps and specialist assignments.
- **Retry/skip/abort on step failure** — if a step throws an exception, the user is asked
  `[r]etry / [s]kip / [a]bort` instead of crashing silently.

### Changed
- Profiles now include `verifikation` (15th profile total)
- Profile selector updated with new entry

---

## [2.3.0] — 2026-04-05

### Added
- **Agent Profiles** (`profiles.py`) — 14 built-in personas activated with `/profile` or
  `/profile <id>`. Each profile appends a focused system-prompt extension.
  Active profile is shown in the startup status line and injected into every prompt.

  | ID | Profil | Zweck |
  |---|---|---|
  | `standard` | 🤖 Standard | Ausgewogener Allzweck-Assistent |
  | `vibe` | ⚡ Vibe-Coder | Einfach machen, keine langen Erklärungen |
  | `aufraumen` | 🏗️ Aufräumen & Strukturieren | Monolith → saubere Module |
  | `reviewer` | 🔍 Code-Reviewer | Feedback geben, keinen Code schreiben |
  | `debugger` | 🐛 Fehlersuche | Bugs methodisch finden und beheben |
  | `erklarer` | 📖 Erklärer | Alles in einfacher Sprache ohne Jargon |
  | `frontend` | 🎨 Frontend | HTML, CSS, JS — schön und bedienbar |
  | `backend` | ⚙️ Backend | APIs, Datenbanken, Server |
  | `tester` | 🧪 Tester | Sinnvolle Tests schreiben |
  | `security` | 🛡️ Sicherheit | Schwachstellen methodisch prüfen |
  | `docs` | 📝 Dokumentation | README, Kommentare, API-Docs |
  | `performance` | 🚀 Performance | Engpässe finden und beheben |
  | `architect` | 🏛️ Architekt | Erst planen, dann bauen |
  | `devops` | 🐳 DevOps | Docker, CI/CD, Deployment |

---

## [2.2.0] — 2026-04-05

### Added
- **Mission Mode** (`mission.py`) — give the agent a high-level goal; it creates a
  numbered plan (up to 8 steps), asks for confirmation, executes each step via a
  separate `agent_loop` call, pauses between steps, and prints a completion summary.
  Available as `/mission <goal>` and `local-cli --mission "goal"`.
- **Auto-Test-Loop** (`autotest.py`) — after every `write_file` / `edit_file`, the
  configured test command runs automatically. Pass/fail output is appended to the
  tool result so the agent self-corrects without any user input.
  Available as `/autotest <cmd>` / `/autotest off` / `/autotest status`.

---

## [2.1.0] — 2026-04-05

### Added
- **Undo system** (`undo.py`) — automatic file snapshots before every `write_file` / `edit_file`;
  `/undo [n]` restores the last n changes, `/checkpoint [name]` sets a manual restore point.
  Up to 30 checkpoints kept per session.
- **Project memory** (`project.py`) — detects Python, Node.js, Rust, Go, Java, .NET, Flutter, PHP,
  Ruby projects automatically; reads metadata from `pyproject.toml`, `package.json`, `Cargo.toml`,
  `go.mod`; extracts git branch, last commit, README summary, test framework; injects a
  `--- PROJECT CONTEXT ---` block into every system prompt. Results cached via mtime fingerprint.
- **Watch mode** (`watcher.py`) — polls a path every 2 s using `os.stat()` (no extra deps);
  triggers the agent automatically on any file change; `/watch <path> <instruction>` slash command
  and `local-cli --watch <path> <instruction>` CLI flag; `/watch stop` / `/watch status`.
- `diff` tool — shows a unified diff of proposed changes before applying them
- `git` tool — safe git operations (status, diff, log, add, commit, branch, stash);
  permanently blocks `push --force`, `reset --hard`, `clean -f`, `branch -D`
- `open` tool — opens a file or URL in the OS default application (cross-platform)

### Changed
- Version bumped to 2.1.0 in `constants.py`, `pyproject.toml`, README badge

---

## [2.0.0] — 2026-04-05

### Breaking Changes
- **Backend replaced**: llama-cpp-python removed. Now requires Ollama or LM Studio.
- **Python requirement raised**: 3.8 → 3.10 (needed for `str | None` type syntax).
- **Model config format changed**: file path → `"ollama:model-id"` / `"lmstudio:model-id"`.

### Added
- `backends.py` — full Ollama and LM Studio HTTP client with SSE streaming
- Animated spinner (`⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏ Generiere...`) while waiting for model response
- `<|think|>` / `<|/think|>` block filtering for reasoning models (QwQ, DeepSeek-R1, etc.)
- Markdown tool extraction fallback — models that output code blocks instead of JSON tool-calls are handled automatically
- Model compatibility check — warns if a loaded model is unsuitable for agent tasks
- Model auto-select — when exactly one model is loaded (e.g. LM Studio), no dialog is shown
- `/save` command — exports current conversation as a timestamped Markdown file
- `/model` command — switch model mid-session without restarting
- `/compact` command — summarizes the conversation to reduce token usage
- `self_improve`: mandatory backup before any edit; syntax validation before any `.py` write
- `self_improve`: `file` parameter to target any `.py` file in the package
- `/reload`: validates syntax of all package files before restarting

### Changed
- Timeout split into connect (10 s) + stream (300 s) to prevent false disconnects on slow models
- Automatic retry on `ConnectionError` (1 attempt) with user-visible message
- System prompt: German language now enforced as first line
- Banner replaced with ASCII-safe design (no Unicode box characters)
- `/tokens` without argument now shows current value and usage hint
- `install.bat`: Python 3.10 check, `pip install --upgrade`, Ollama model check, LM Studio start instructions, dynamic summary
- `uninstall.bat`: checks if package is installed first, clarifies data location, documents what is NOT removed

### Removed
- `/thinking` command (was a no-op — parameter never reached the backend)
- llama-cpp-python dependency
- `local_backend.py` (replaced by `backends.py`)
- NVIDIA NIM / Kimi K2.5 references

### Fixed
- Banner alignment broken by ANSI codes inside padded f-strings
- Empty model list crash when no backend is running
- `self_improve` backup failure was silently ignored

---

## [1.3.0] — 2026-03-19

### Changed
- Complete rebranding from kimi-k-cli to local-cli-agent
- Added slash command autocomplete via prompt_toolkit
- Migrated from NVIDIA NIM API to local model backends

---

## [1.2.0] — 2026-03-18

### Removed
- Plugin system (too fragile, low benefit)

### Fixed
- Startup errors on fresh install

---

## [1.1.0] — 2026-03-17

### Added
- Initial release as Kimi K2.5 CLI agent
- Tool use: bash, file ops, web search, memory, self-improve
- Interactive and one-shot modes
