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
from local_cli_agent.web import strip_html
from local_cli_agent.memory import load_memory, save_memory_file
from local_cli_agent.changelog import add_changelog_entry, get_changelog

# ── Auto-approve mode ───────────────────────────────────────────────────────
auto_approve = False


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
        if not ask_permission("write_file", f"{path} ({len(content)} chars)"):
            return "User denied execution."
        try:
            abs_path = os.path.abspath(path)
            os.makedirs(os.path.dirname(abs_path) or ".", exist_ok=True)
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f" {DIM}Wrote {len(content)} chars -> {abs_path}{RESET}")
            return f"File written: {abs_path}"
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
        new_content = content.replace(old_string, new_string, 1)
        try:
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f" {DIM}Edited {abs_path}{RESET}")
            return f"File edited: {abs_path}"
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
        if action == "version":
            return f"Local CLI Agent v{VERSION}\nSource: {SCRIPT_FILE}"
        elif action == "read_source":
            print(f" {DIM}Reading own source code...{RESET}")
            try:
                with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
                    content = f.read()
                lines = content.split("\n")
                print(f" {DIM}{len(lines)} lines, {len(content)} chars{RESET}")
                return content
            except Exception as e:
                return f"Error reading source: {e}"
        elif action == "edit_source":
            old_string = args.get("old_string", "")
            new_string = args.get("new_string", "")
            if not old_string or not new_string:
                return "Error: old_string and new_string required."
            try:
                with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                return f"Error reading source: {e}"
            count = content.count(old_string)
            if count == 0:
                return "Error: old_string not found in source code."
            if count > 1:
                return f"Error: old_string found {count} times. Be more specific."
            preview = f"Replace '{old_string[:50]}...' -> '{new_string[:50]}...'"
            if not ask_permission("self_improve:edit_source", preview):
                return "User denied."
            backup_path = SCRIPT_FILE + f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            try:
                with open(backup_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f" {DIM}Backup: {backup_path}{RESET}")
            except Exception:
                pass
            new_content = content.replace(old_string, new_string, 1)
            try:
                with open(SCRIPT_FILE, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f" {GREEN}Source code updated. Use /reload to apply.{RESET}")
                return f"Source edited successfully. Backup at: {backup_path}\nIMPORTANT: Tell the user to run /reload to apply changes."
            except Exception as e:
                return f"Error writing source: {e}"
        elif action == "backup":
            backup_path = SCRIPT_FILE + f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            try:
                with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
                    content = f.read()
                with open(backup_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f" {DIM}Backup saved: {backup_path}{RESET}")
                return f"Backup created: {backup_path}"
            except Exception as e:
                return f"Error: {e}"
        elif action == "changelog":
            entry = args.get("changelog_entry", "")
            if entry:
                add_changelog_entry(entry)
                return "Changelog entry added."
            else:
                return get_changelog()
        return f"Unknown self_improve action: {action}"

    # ── unknown ──────────────────────────────────────────────────────────
    else:
        return f"Unknown tool: {name}"
