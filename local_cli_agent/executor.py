# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Steffen Schwabe
import ast
import difflib
import os
import sys
import json
import re
import subprocess
import glob as glob_module
from datetime import datetime
from urllib.parse import unquote

import requests

from local_cli_agent.constants import (
    RESET, BOLD, DIM, CYAN, GREEN, YELLOW, MAGENTA, RED,
    VERSION, SCRIPT_FILE,
)

# ── Package directory (for self_improve file validation) ────────────────────
_PKG_DIR = os.path.dirname(os.path.abspath(__file__))


def _check_python_syntax(code: str, filename: str = "<string>") -> str | None:
    """Returns None if syntax is valid, or an error message string."""
    try:
        ast.parse(code)
        return None
    except SyntaxError as e:
        return f"Syntax-Fehler in {filename} (Zeile {e.lineno}): {e.msg}"
from local_cli_agent.web import strip_html
from local_cli_agent.memory import load_memory, save_memory_file
from local_cli_agent.changelog import add_changelog_entry, get_changelog
from local_cli_agent import undo as _undo
from local_cli_agent import autotest as _autotest

# ── Auto-approve mode ───────────────────────────────────────────────────────
auto_approve = False


# ── Git Auto-Commit ──────────────────────────────────────────────────────────
def _git_autocommit(abs_path: str, action: str) -> None:
    """Stage and commit a single file when git_autocommit setting is enabled."""
    from local_cli_agent import settings as _settings
    if not _settings.get("git_autocommit"):
        return
    # Check we are inside a git repo
    check = subprocess.run(
        "git rev-parse --is-inside-work-tree",
        shell=True, capture_output=True, cwd=os.getcwd(),
    )
    if check.returncode != 0:
        return
    try:
        rel = os.path.relpath(abs_path, os.getcwd())
    except ValueError:
        rel = abs_path
    msg = f"agent: {action} {rel}"
    # shell=False + Argumente als Liste: sicher bei Dateinamen mit Leerzeichen/Sonderzeichen
    subprocess.run(
        ["git", "add", abs_path],
        capture_output=True, cwd=os.getcwd(),
    )
    result = subprocess.run(
        ["git", "commit", "-m", msg],
        capture_output=True, text=True,
        encoding="utf-8", errors="replace", cwd=os.getcwd(),
    )
    if result.returncode == 0:
        print(f" {DIM}[git] committed: {rel}{RESET}")


def ask_permission(tool_name, details):
    """Ask user for permission before executing a tool."""
    global auto_approve
    if auto_approve:
        print(f" {DIM}{YELLOW}[auto] {tool_name}: {details[:100]}{RESET}")
        return True
    print(f"\n{YELLOW}{BOLD} Tool: {tool_name}{RESET}")
    print(f" {DIM}{details[:200]}{RESET}")
    print(f" {YELLOW}Execute? {RESET}[{BOLD}y{RESET}]es / [{BOLD}n{RESET}]o / [{BOLD}a{RESET}]lways: ", end="", flush=True)
    try:
        choice = input().strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False
    if choice in ("a", "always"):
        auto_approve = True
        return True
    return choice in ("y", "yes", "")


def show_output(text, max_lines=30):
    """Display tool output to user."""
    lines = text.strip().split("\n")
    for line in lines[:max_lines]:
        print(f" {DIM}{line}{RESET}")
    if len(lines) > max_lines:
        print(f" {DIM}... ({len(lines)} lines total){RESET}")


def execute_tool(name, arguments):
    """Execute a tool and return the result."""
    try:
        args = json.loads(arguments) if isinstance(arguments, str) else arguments
    except json.JSONDecodeError:
        return f"Error: Invalid tool arguments: {arguments}"

    # ── bash ─────────────────────────────────────────────────────────────
    if name == "bash":
        command = args.get("command", "")
        if not ask_permission("bash", command):
            return "User denied execution."
        print(f" {DIM}$ {command}{RESET}")
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=120,
                cwd=os.getcwd(), encoding="utf-8", errors="replace",
            )
            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                output += ("\n" if output else "") + result.stderr
            if result.returncode != 0:
                output += f"\n[exit code: {result.returncode}]"
            if not output.strip():
                output = "[command completed successfully]"
            show_output(output)
            return output[:10000]
        except subprocess.TimeoutExpired:
            print(f" {RED}Command timed out (120s){RESET}")
            return "Error: Command timed out after 120 seconds."
        except Exception as e:
            print(f" {RED}Error: {e}{RESET}")
            return f"Error: {e}"

    # ── write_file ───────────────────────────────────────────────────────
    elif name == "write_file":
        path = args.get("path", "")
        content = args.get("content", "")
        # ── Syntax guard for Python files ────────────────────────────────
        if path.endswith(".py"):
            err = _check_python_syntax(content, path)
            if err:
                print(f" {RED}Schreiben abgebrochen:{RESET} {err}")
                return f"Fehler: {err}\nDatei wurde NICHT gespeichert."
        if not ask_permission("write_file", f"{path} ({len(content)} chars)"):
            return "User denied execution."
        try:
            abs_path = os.path.abspath(path)
            _undo.save_checkpoint(f"write_file: {path}", [abs_path])
            os.makedirs(os.path.dirname(abs_path) or ".", exist_ok=True)
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f" {DIM}Wrote {len(content)} chars -> {abs_path}{RESET}")
            result = f"File written: {abs_path}"
            if _autotest.is_enabled():
                passed, test_out = _autotest.run()
                if passed:
                    result += "\n\n[autotest] Alle Tests bestanden."
                else:
                    result += f"\n\n[autotest] Tests FEHLGESCHLAGEN — bitte korrigieren:\n{test_out}"
            _git_autocommit(abs_path, "write")
            return result
        except Exception as e:
            print(f" {RED}Error: {e}{RESET}")
            return f"Error: {e}"

    # ── edit_file ────────────────────────────────────────────────────────
    elif name == "edit_file":
        path = args.get("path", "")
        old_string = args.get("old_string", "")
        new_string = args.get("new_string", "")
        abs_path = os.path.abspath(path)
        if not os.path.exists(abs_path):
            return f"Error: File not found: {abs_path}"
        try:
            with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            return f"Error reading file: {e}"
        count = content.count(old_string)
        if count == 0:
            return f"Error: String not found in {abs_path}. Make sure old_string matches exactly (including whitespace)."
        if count > 1:
            return f"Error: String found {count} times in {abs_path}. Provide more context to make it unique."
        preview = f"{path}: replace '{old_string[:60]}...' with '{new_string[:60]}...'" if len(old_string) > 60 else f"{path}: '{old_string}' -> '{new_string}'"
        if not ask_permission("edit_file", preview):
            return "User denied execution."
        _undo.save_checkpoint(f"edit_file: {path}", [abs_path])
        new_content = content.replace(old_string, new_string, 1)
        # ── Syntax guard for Python files ────────────────────────────────
        if abs_path.endswith(".py"):
            err = _check_python_syntax(new_content, path)
            if err:
                print(f" {RED}Bearbeitung abgebrochen:{RESET} {err}")
                return f"Fehler: {err}\nDatei wurde NICHT verändert."
        try:
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f" {DIM}Edited {abs_path}{RESET}")
            result = f"File edited: {abs_path}"
            if _autotest.is_enabled():
                passed, test_out = _autotest.run()
                if passed:
                    result += "\n\n[autotest] Alle Tests bestanden."
                else:
                    result += f"\n\n[autotest] Tests FEHLGESCHLAGEN — bitte korrigieren:\n{test_out}"
            _git_autocommit(abs_path, "edit")
            return result
        except Exception as e:
            return f"Error writing file: {e}"

    # ── read_file ────────────────────────────────────────────────────────
    elif name == "read_file":
        path = args.get("path", "")
        abs_path = os.path.abspath(path)
        print(f" {DIM}Reading {abs_path}{RESET}")
        try:
            with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            if len(content) > 20000:
                content = content[:20000] + f"\n... [truncated, {len(content)} chars total]"
            return content if content else "[empty file]"
        except FileNotFoundError:
            return f"Error: File not found: {abs_path}"
        except Exception as e:
            return f"Error: {e}"

    # ── list_directory ───────────────────────────────────────────────────
    elif name == "list_directory":
        path = args.get("path", ".")
        abs_path = os.path.abspath(path)
        print(f" {DIM}Listing {abs_path}{RESET}")
        try:
            entries = os.listdir(abs_path)
            lines = []
            for entry in sorted(entries):
                full = os.path.join(abs_path, entry)
                if os.path.isdir(full):
                    lines.append(f" {entry}/")
                else:
                    size = os.path.getsize(full)
                    lines.append(f" {entry} ({size} bytes)")
            output = "\n".join(lines) if lines else "[empty directory]"
            show_output(output)
            return output
        except FileNotFoundError:
            return f"Error: Not found: {abs_path}"
        except Exception as e:
            return f"Error: {e}"

    # ── grep_search ──────────────────────────────────────────────────────
    elif name == "grep_search":
        pattern = args.get("pattern", "")
        search_path = args.get("path", ".")
        file_pattern = args.get("file_pattern", None)
        ignore_case = args.get("ignore_case", False)
        abs_path = os.path.abspath(search_path)
        print(f" {DIM}Searching '{pattern}' in {abs_path}{RESET}")
        flags = re.IGNORECASE if ignore_case else 0
        try:
            compiled = re.compile(pattern, flags)
        except re.error as e:
            return f"Error: Invalid regex: {e}"
        results = []
        max_results = 50
        skip_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv", ".tox", "dist", "build"}
        for root, dirs, files in os.walk(abs_path):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for fname in files:
                if file_pattern and not glob_module.fnmatch.fnmatch(fname, file_pattern):
                    continue
                fpath = os.path.join(root, fname)
                rel_path = os.path.relpath(fpath, abs_path)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                        for i, line in enumerate(f, 1):
                            if compiled.search(line):
                                results.append(f"{rel_path}:{i}: {line.rstrip()}")
                                if len(results) >= max_results:
                                    break
                except (IOError, UnicodeDecodeError):
                    continue
                if len(results) >= max_results:
                    break
            if len(results) >= max_results:
                break
        if not results:
            output = f"No matches found for '{pattern}'"
        else:
            output = "\n".join(results)
            if len(results) == max_results:
                output += f"\n... (limited to {max_results} results)"
        show_output(output)
        return output

    # ── glob_find ────────────────────────────────────────────────────────
    elif name == "glob_find":
        pattern = args.get("pattern", "")
        base_path = args.get("path", ".")
        abs_path = os.path.abspath(base_path)
        print(f" {DIM}Finding '{pattern}' in {abs_path}{RESET}")
        full_pattern = os.path.join(abs_path, pattern)
        matches = sorted(glob_module.glob(full_pattern, recursive=True))
        skip = {".git", "node_modules", "__pycache__", ".venv"}
        filtered = []
        for m in matches:
            parts = m.replace("\\", "/").split("/")
            if not any(p in skip for p in parts):
                filtered.append(os.path.relpath(m, abs_path))
        if not filtered:
            output = f"No files found matching '{pattern}'"
        else:
            output = "\n".join(filtered[:100])
            if len(filtered) > 100:
                output += f"\n... ({len(filtered)} files total)"
        show_output(output)
        return output

    # ── web_search ───────────────────────────────────────────────────────
    elif name == "web_search":
        query = args.get("query", "")
        num_results = min(args.get("num_results", 5), 10)
        if not ask_permission("web_search", f'Searching: "{query}"'):
            return "User denied execution."
        print(f" {DIM}Searching: {query}{RESET}")
        try:
            resp = requests.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                timeout=15,
            )
            resp.raise_for_status()
            html = resp.text
            results = []
            blocks = re.findall(
                r'<a rel="nofollow" class="result__a" href="([^"]*)"[^>]*>(.*?)</a>.*?'
                r'<a class="result__snippet"[^>]*>(.*?)</a>',
                html, re.DOTALL
            )
            for url, title, snippet in blocks[:num_results]:
                title = re.sub(r'<[^>]+>', '', title).strip()
                snippet = re.sub(r'<[^>]+>', '', snippet).strip()
                actual_url = url
                if "uddg=" in url:
                    match = re.search(r'uddg=([^&]+)', url)
                    if match:
                        actual_url = unquote(match.group(1))
                results.append(f"[{title}]\n URL: {actual_url}\n {snippet}")
            if results:
                output = "\n\n".join(results)
            else:
                output = f"No results found for '{query}'"
            show_output(output, max_lines=40)
            return output
        except Exception as e:
            print(f" {RED}Search error: {e}{RESET}")
            return f"Error searching: {e}"

    # ── web_fetch ────────────────────────────────────────────────────────
    elif name == "web_fetch":
        url = args.get("url", "")
        max_length = args.get("max_length", 15000)
        if not ask_permission("web_fetch", url):
            return "User denied execution."
        print(f" {DIM}Fetching: {url}{RESET}")
        try:
            resp = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                timeout=20,
                allow_redirects=True,
            )
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "")
            if "json" in content_type:
                try:
                    text = json.dumps(resp.json(), indent=2, ensure_ascii=False)
                except Exception:
                    text = resp.text
            elif "html" in content_type:
                text = strip_html(resp.text)
            else:
                text = resp.text
            if len(text) > max_length:
                text = text[:max_length] + f"\n... [truncated, {len(text)} chars total]"
            line_count = len(text.split("\n"))
            print(f" {DIM}Fetched {len(text)} chars, {line_count} lines{RESET}")
            return text
        except requests.exceptions.Timeout:
            return f"Error: Request timed out for {url}"
        except requests.exceptions.HTTPError as e:
            return f"Error: HTTP {e.response.status_code} for {url}"
        except Exception as e:
            return f"Error fetching {url}: {e}"

    # ── memory ───────────────────────────────────────────────────────────
    elif name == "memory":
        action = args.get("action", "list")
        mem = load_memory()
        if action == "save":
            key = args.get("key", "")
            content = args.get("content", "")
            if not key or not content:
                return "Error: 'key' and 'content' are required for save."
            mem[key] = {
                "content": content,
                "saved_at": datetime.now().isoformat(),
            }
            save_memory_file(mem)
            print(f" {DIM}Memory saved: '{key}'{RESET}")
            return f"Saved memory '{key}'"
        elif action == "recall":
            key = args.get("key", "")
            query = args.get("query", key or "")
            if not query:
                return "Error: 'key' or 'query' required for recall."
            if query in mem:
                entry = mem[query]
                result = f"[{query}] (saved {entry['saved_at']})\n{entry['content']}"
                print(f" {DIM}Recalled: '{query}'{RESET}")
                return result
            matches = []
            query_lower = query.lower()
            for k, v in mem.items():
                if query_lower in k.lower() or query_lower in v["content"].lower():
                    matches.append(f"[{k}] (saved {v['saved_at']})\n{v['content']}")
            if matches:
                print(f" {DIM}Found {len(matches)} memory match(es){RESET}")
                return "\n\n---\n\n".join(matches)
            return f"No memories found matching '{query}'"
        elif action == "list":
            if not mem:
                return "No memories saved yet."
            lines = []
            for k, v in mem.items():
                preview = v["content"][:80].replace("\n", " ")
                lines.append(f" [{k}] {preview}... ({v['saved_at']})")
            output = "\n".join(lines)
            show_output(output)
            return output
        elif action == "delete":
            key = args.get("key", "")
            if key in mem:
                del mem[key]
                save_memory_file(mem)
                print(f" {DIM}Deleted memory: '{key}'{RESET}")
                return f"Deleted memory '{key}'"
            return f"Memory '{key}' not found."
        return f"Unknown memory action: {action}"

    # ── self_improve ─────────────────────────────────────────────────────
    elif name == "self_improve":
        action = args.get("action", "version")

        # Resolve target file: any .py inside the package dir, default = SCRIPT_FILE
        raw_file = args.get("file", "")
        if raw_file:
            target_file = os.path.normpath(os.path.join(_PKG_DIR, os.path.basename(raw_file)))
            if not target_file.startswith(_PKG_DIR) or not target_file.endswith(".py"):
                return f"Fehler: Nur .py-Dateien im Paketverzeichnis erlaubt ({_PKG_DIR})"
        else:
            target_file = SCRIPT_FILE

        if action == "version":
            py_files = sorted(os.path.basename(f) for f in glob_module.glob(os.path.join(_PKG_DIR, "*.py")))
            return (
                f"Local CLI Agent v{VERSION}\n"
                f"Paketverzeichnis: {_PKG_DIR}\n"
                f"Bearbeitbare Dateien: {', '.join(py_files)}"
            )

        elif action == "read_source":
            print(f" {DIM}Lese Quellcode: {os.path.basename(target_file)}...{RESET}")
            try:
                with open(target_file, "r", encoding="utf-8") as f:
                    content = f.read()
                lines = content.split("\n")
                print(f" {DIM}{len(lines)} Zeilen, {len(content)} Zeichen{RESET}")
                return content
            except Exception as e:
                return f"Fehler beim Lesen: {e}"

        elif action == "edit_source":
            old_string = args.get("old_string", "")
            new_string = args.get("new_string", "")
            if not old_string or not new_string:
                return "Fehler: old_string und new_string sind erforderlich."
            try:
                with open(target_file, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                return f"Fehler beim Lesen: {e}"
            count = content.count(old_string)
            if count == 0:
                return "Fehler: old_string nicht im Quellcode gefunden."
            if count > 1:
                return f"Fehler: old_string kommt {count}x vor – bitte eindeutiger formulieren."

            new_content = content.replace(old_string, new_string, 1)

            # ── PFLICHT: Syntax-Check vor dem Schreiben ───────────────────
            syntax_err = _check_python_syntax(new_content, os.path.basename(target_file))
            if syntax_err:
                print(f" {RED}Schreiben abgebrochen – Syntax-Fehler:{RESET} {syntax_err}")
                return (
                    f"ABGEBROCHEN: {syntax_err}\n"
                    "Die Datei wurde NICHT verändert. Bitte old_string/new_string korrigieren."
                )

            preview = f"{os.path.basename(target_file)}: '{old_string[:50]}' → '{new_string[:50]}'"
            if not ask_permission("self_improve:edit_source", preview):
                return "Abgebrochen durch Benutzer."

            # ── PFLICHT: Backup (Fehler = Abbruch) ────────────────────────
            backup_path = target_file + f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            try:
                with open(backup_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f" {DIM}Backup: {backup_path}{RESET}")
            except Exception as e:
                return f"ABGEBROCHEN: Backup fehlgeschlagen ({e}). Datei wurde NICHT verändert."

            try:
                with open(target_file, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f" {GREEN}Quellcode aktualisiert: {os.path.basename(target_file)}{RESET}")
                return (
                    f"Erfolgreich bearbeitet: {os.path.basename(target_file)}\n"
                    f"Backup: {backup_path}\n"
                    "WICHTIG: /reload ausführen, damit die Änderungen aktiv werden."
                )
            except Exception as e:
                return f"Fehler beim Schreiben: {e}"

        elif action == "backup":
            backup_path = target_file + f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            try:
                with open(target_file, "r", encoding="utf-8") as f:
                    content = f.read()
                with open(backup_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f" {DIM}Backup gespeichert: {backup_path}{RESET}")
                return f"Backup erstellt: {backup_path}"
            except Exception as e:
                return f"Fehler: {e}"

        elif action == "changelog":
            entry = args.get("changelog_entry", "")
            if entry:
                add_changelog_entry(entry)
                return "Changelog-Eintrag hinzugefügt."
            else:
                return get_changelog()

        return f"Unbekannte self_improve-Aktion: {action}"

    # ── diff ─────────────────────────────────────────────────────────────
    elif name == "diff":
        path = args.get("path", "")
        old_string = args.get("old_string", "")
        new_string = args.get("new_string", "")
        abs_path = os.path.abspath(path)
        if not os.path.exists(abs_path):
            return f"Error: File not found: {abs_path}"
        try:
            with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            return f"Error reading file: {e}"
        if not content.count(old_string):
            return f"String not found in {path} — nothing to diff."
        new_content = content.replace(old_string, new_string, 1)
        lines = list(difflib.unified_diff(
            content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=f"{path}  (vorher)",
            tofile=f"{path}  (nachher)",
            lineterm="",
        ))
        if not lines:
            return "Keine Änderungen (old_string und new_string sind identisch)."
        output = "".join(lines)
        show_output(output, max_lines=60)
        return output

    # ── git ──────────────────────────────────────────────────────────────
    elif name == "git":
        action = args.get("action", "status")

        # ── Permanently blocked operations ───────────────────────────────
        _BLOCKED = {
            "push --force", "push -f",
            "reset --hard", "reset -h",
            "clean -f", "clean -fd", "clean -fx",
            "checkout --",
            "branch -D", "branch -d",
        }

        if action == "status":
            cmd = "git status"
        elif action == "diff":
            target = args.get("target", "")
            cmd = f"git diff {target}".strip()
        elif action == "log":
            count = int(args.get("count", 10))
            cmd = f"git log --oneline -{count}"
        elif action == "add":
            files = args.get("files", ".")
            cmd = f"git add {files}"
        elif action == "commit":
            message = args.get("message", "")
            if not message:
                return "Error: 'message' is required for commit."
            safe_msg = message.replace('"', '\\"')
            cmd = f'git commit -m "{safe_msg}"'
        elif action == "branch":
            cmd = "git branch"
        elif action == "stash":
            sub = args.get("subcommand", "list")
            if sub not in ("list", "pop", "push"):
                return "Error: stash subcommand must be 'list', 'push', or 'pop'."
            cmd = f"git stash {sub}"
        else:
            return (
                f"Error: unknown git action '{action}'. "
                "Allowed: status, diff, log, add, commit, branch, stash"
            )

        cmd_lower = cmd.lower()
        for blocked in _BLOCKED:
            if blocked in cmd_lower:
                return f"Error: '{blocked}' is blocked for safety. Use bash if you are sure."

        print(f" {DIM}$ {cmd}{RESET}")
        if not ask_permission("git", cmd):
            return "User denied execution."
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30,
                cwd=os.getcwd(), encoding="utf-8", errors="replace",
            )
            output = result.stdout
            if result.stderr:
                output += ("\n" if output else "") + result.stderr
            if result.returncode != 0:
                output += f"\n[exit code: {result.returncode}]"
            if not output.strip():
                output = "[git command completed, no output]"
            show_output(output)
            return output[:5000]
        except Exception as e:
            return f"Error: {e}"

    # ── open ─────────────────────────────────────────────────────────────
    elif name == "open":
        path = args.get("path", "")
        is_url = path.startswith(("http://", "https://"))
        target = path if is_url else os.path.abspath(path)
        if not is_url and not os.path.exists(target):
            return f"Error: File not found: {target}"
        if not ask_permission("open", target):
            return "User denied execution."
        try:
            if sys.platform == "win32":
                os.startfile(target)
            elif sys.platform == "darwin":
                subprocess.run(["open", target], check=True)
            else:
                subprocess.run(["xdg-open", target], check=True)
            print(f" {DIM}Opened: {target}{RESET}")
            return f"Opened: {target}"
        except Exception as e:
            return f"Error opening {target}: {e}"

    # ── unknown ──────────────────────────────────────────────────────────
    else:
        return f"Unknown tool: {name}"