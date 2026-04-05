# Changelog

All notable changes to Local CLI Agent are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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
