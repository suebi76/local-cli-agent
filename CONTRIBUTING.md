# Contributing to Local CLI Agent

[🇬🇧 English](#english) · [🇩🇪 Deutsch](#deutsch)

---

<a name="english"></a>
## 🇬🇧 English

Thank you for your interest in contributing! Here is everything you need to get started.

### Ways to Contribute

- **Report a bug** — use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md)
- **Suggest a feature** — use the [feature request template](.github/ISSUE_TEMPLATE/feature_request.md)
- **Fix a bug** — open a PR with a fix and a short description of the problem
- **Add a tool** — new tools go in `executor.py` (handler) and `tools.py` (schema)
- **Improve tests** — the `tests/` directory uses pytest, all tests run offline

### Development Setup

```bash
git clone https://github.com/suebi76/local-cli-agent.git
cd local-cli-agent
pip install -e ".[dev]"
```

Requirements: Python 3.10+, Ollama or LM Studio running locally.

### Running Tests

```bash
pytest tests/ -v
```

All tests are fully offline — no model backend required.

### Code Style

- Linter: [Ruff](https://docs.astral.sh/ruff/) — `ruff check local_cli_agent/`
- Line length: 100 characters
- Target: Python 3.10+
- Dependencies: only `requests` and `prompt_toolkit` (keep it lean)
- Every source file must start with the SPDX license header

### Project Structure

```
local_cli_agent/
  backends.py       — Ollama & LM Studio HTTP client, SSE streaming
  model_selector.py — interactive model picker (prompt_toolkit dialog)
  api.py            — thin wrapper: active model state, call_api()
  agent.py          — agent loop, markdown tool-call extraction fallback
  executor.py       — tool implementations, permission prompt, self-improve
  tools.py          — OpenAI-format tool schemas + formatting rules
  ui.py             — interactive mode, slash command handling
  cli.py            — entry point (argparse)
  config.py         — system prompt builder, last model persistence
  constants.py      — ANSI codes, file paths, VERSION
  memory.py         — persistent key-value memory (JSON file)
  changelog.py      — self-improvement changelog (JSON file)
  web.py            — HTML stripper for web_fetch tool
  _env.py           — .env file loader

tests/              — pytest test suite (offline)
install.bat / .sh   — platform installers
uninstall.bat / .sh — platform uninstallers
```

### Adding a New Tool

1. **`tools.py`** — add an entry to the `TOOLS` list (OpenAI function schema)
2. **`executor.py`** — add a handler in `execute_tool()`:
   ```python
   elif name == "my_tool":
       arg = args.get("arg", "")
       if not ask_permission("my_tool", arg):
           return "User denied."
       # ... implementation ...
       return result
   ```
3. **Tests** — add a test in `tests/test_executor.py`

### Pull Request Guidelines

- Keep PRs focused — one topic per PR
- Add or update tests for any changed behaviour
- Run `pytest tests/ -v` and `ruff check local_cli_agent/` before submitting
- Describe what problem your PR solves in the PR description
- Use English for code, comments, and PR descriptions

### License

By contributing, you agree that your contributions will be licensed under the
[MIT License](LICENSE).

---

<a name="deutsch"></a>
## 🇩🇪 Deutsch

Danke für dein Interesse am Mithelfen! Hier ist alles, was du zum Einstieg brauchst.

### Möglichkeiten zur Mitarbeit

- **Fehler melden** — [Bug-Report-Vorlage](.github/ISSUE_TEMPLATE/bug_report.md) verwenden
- **Feature vorschlagen** — [Feature-Request-Vorlage](.github/ISSUE_TEMPLATE/feature_request.md) verwenden
- **Fehler beheben** — PR mit Fix und kurzer Beschreibung des Problems öffnen
- **Tool hinzufügen** — neue Tools kommen in `executor.py` (Handler) und `tools.py` (Schema)
- **Tests verbessern** — das `tests/`-Verzeichnis nutzt pytest, alle Tests laufen offline

### Entwicklungsumgebung einrichten

```bash
git clone https://github.com/suebi76/local-cli-agent.git
cd local-cli-agent
pip install -e ".[dev]"
```

Voraussetzungen: Python 3.10+, Ollama oder LM Studio lokal laufend.

### Tests ausführen

```bash
pytest tests/ -v
```

Alle Tests laufen vollständig offline — kein Modell-Backend erforderlich.

### Code-Stil

- Linter: [Ruff](https://docs.astral.sh/ruff/) — `ruff check local_cli_agent/`
- Zeilenlänge: 100 Zeichen
- Ziel: Python 3.10+
- Abhängigkeiten: nur `requests` und `prompt_toolkit` (schlank halten)
- Jede Quelldatei muss mit dem SPDX-Lizenz-Header beginnen

### Neues Tool hinzufügen

1. **`tools.py`** — Eintrag zur `TOOLS`-Liste hinzufügen (OpenAI Function Schema)
2. **`executor.py`** — Handler in `execute_tool()` hinzufügen:
   ```python
   elif name == "mein_tool":
       arg = args.get("arg", "")
       if not ask_permission("mein_tool", arg):
           return "User denied."
       # ... Implementierung ...
       return result
   ```
3. **Tests** — Test in `tests/test_executor.py` hinzufügen

### Pull-Request-Richtlinien

- PRs fokussiert halten — ein Thema pro PR
- Tests für geänderte Funktionalität hinzufügen oder aktualisieren
- Vor dem Einreichen `pytest tests/ -v` und `ruff check local_cli_agent/` ausführen
- Im PR beschreiben, welches Problem gelöst wird
- Code, Kommentare und PR-Beschreibungen auf Englisch

### Lizenz

Mit deinem Beitrag stimmst du zu, dass deine Änderungen unter der
[MIT-Lizenz](LICENSE) veröffentlicht werden.
