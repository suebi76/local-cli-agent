# Contributing to Local CLI Agent

Thank you for your interest in contributing! This document explains how to get
involved and what to expect.

---

## Ways to Contribute

- **Report a bug** — use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md)
- **Suggest a feature** — use the [feature request template](.github/ISSUE_TEMPLATE/feature_request.md)
- **Fix a bug** — open a PR with a fix and a short description of the problem
- **Add a tool** — new tools go in `executor.py` (handler) and `tools.py` (schema)
- **Improve tests** — the `tests/` directory uses pytest

---

## Development Setup

```bash
git clone https://github.com/suebi76/local-cli-agent.git
cd local-cli-agent
pip install -e ".[dev]"
```

Requirements: Python 3.10+, Ollama or LM Studio running locally.

---

## Running Tests

```bash
pytest tests/ -v
```

Tests are fully offline — no model backend required.

---

## Code Style

- Formatter / linter: [Ruff](https://docs.astral.sh/ruff/) (`ruff check local_cli_agent/`)
- Line length: 100 characters
- Target: Python 3.10+
- No external dependencies beyond `requests` and `prompt_toolkit`

---

## Project Structure

```
local_cli_agent/
  backends.py       — Ollama & LM Studio HTTP client, SSE streaming
  model_selector.py — interactive model picker (prompt_toolkit dialog)
  api.py            — thin wrapper: set active model, call_api()
  agent.py          — agent loop, markdown tool extraction fallback
  executor.py       — tool implementations, self-improve, permission prompt
  tools.py          — OpenAI-format tool schemas + formatting rules
  ui.py             — interactive mode, slash commands
  cli.py            — entry point (argparse)
  config.py         — system prompt, last model persistence
  constants.py      — ANSI codes, paths, VERSION
  memory.py         — persistent key-value memory (JSON)
  changelog.py      — self-improvement changelog (JSON)
  web.py            — HTML stripper for web_fetch
  _env.py           — .env loader

tests/              — pytest test suite (offline, no model needed)
install.bat         — Windows installer
install.sh          — macOS/Linux installer
uninstall.bat       — Windows uninstaller
uninstall.sh        — macOS/Linux uninstaller
```

---

## Adding a New Tool

1. **`tools.py`** — add an entry to the `TOOLS` list (OpenAI function schema)
2. **`executor.py`** — add a handler block in `execute_tool()`:
   ```python
   elif name == "my_tool":
       arg = args.get("arg", "")
       if not ask_permission("my_tool", arg):
           return "User denied."
       # ... implementation ...
       return result
   ```
3. **Tests** — add a test in `tests/test_executor.py`

---

## Pull Request Guidelines

- Keep PRs focused — one change per PR
- Add or update tests for any changed behaviour
- Run `pytest tests/ -v` and `ruff check local_cli_agent/` before submitting
- Describe what problem your PR solves in the description

---

## License

By contributing, you agree that your contributions will be licensed under the
[MIT License](LICENSE).
