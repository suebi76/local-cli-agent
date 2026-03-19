#!/usr/bin/env python3
"""
Kimi K2.5 Agent CLI - Interactive AI coding assistant with full tool use.
Self-improving AI coding assistant, powered by NVIDIA NIM API.
Tools: bash, files, edit, grep, web search, web fetch, memory.
"""

import sys
import os
import json
import subprocess
import requests
import argparse
import signal
import re
import glob as glob_module
import hashlib
from datetime import datetime
from html.parser import HTMLParser

# Fix Windows console encoding for Unicode output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    os.system("")  # Enable ANSI escape codes on Windows

# ── ANSI Colors ──────────────────────────────────────────────────────────────
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
CYAN    = "\033[36m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
MAGENTA = "\033[35m"
RED     = "\033[31m"
BLUE    = "\033[34m"
WHITE   = "\033[37m"

# ── Config ───────────────────────────────────────────────────────────────────
API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL   = "moonshotai/kimi-k2.5"
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
SCRIPT_FILE  = os.path.abspath(__file__)
ENV_FILE     = os.path.join(SCRIPT_DIR, ".env")
MEMORY_FILE  = os.path.join(SCRIPT_DIR, ".kimi-memory.json")
PLUGINS_DIR  = os.path.join(SCRIPT_DIR, "plugins")
CHANGELOG    = os.path.join(SCRIPT_DIR, ".kimi-changelog.json")
VERSION      = "1.1.0"

# ── Tool Definitions (OpenAI format) ────────────────────────────────────────
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Execute a bash/shell command on the local system. Use for: creating directories, running scripts, installing packages, git commands, compiling code, and any system operations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute"
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or overwrite a file with the given content. Use for creating new files or completely rewriting existing ones.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute or relative file path"
                    },
                    "content": {
                        "type": "string",
                        "description": "The full content to write to the file"
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Edit a file by replacing a specific string with a new string. Use this for targeted edits to existing files instead of rewriting the whole file. The old_string must match exactly (including whitespace/indentation).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path to edit"
                    },
                    "old_string": {
                        "type": "string",
                        "description": "The exact string to find and replace (must be unique in the file)"
                    },
                    "new_string": {
                        "type": "string",
                        "description": "The replacement string"
                    }
                },
                "required": ["path", "old_string", "new_string"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file from the local filesystem.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute or relative file path to read"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files and directories in a given path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path to list (default: current directory)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "grep_search",
            "description": "Search for a pattern (regex) in files. Returns matching lines with file paths and line numbers. Great for finding code, functions, variables, or any text across the codebase.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Regex pattern to search for"
                    },
                    "path": {
                        "type": "string",
                        "description": "Directory or file to search in (default: current directory)"
                    },
                    "file_pattern": {
                        "type": "string",
                        "description": "Glob pattern to filter files, e.g. '*.py', '*.js', '*.ts' (default: all files)"
                    },
                    "ignore_case": {
                        "type": "boolean",
                        "description": "Case insensitive search (default: false)"
                    }
                },
                "required": ["pattern"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "glob_find",
            "description": "Find files matching a glob pattern. Use to discover project structure and find specific files by name or extension.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Glob pattern, e.g. '**/*.py', 'src/**/*.ts', '**/package.json'"
                    },
                    "path": {
                        "type": "string",
                        "description": "Base directory to search from (default: current directory)"
                    }
                },
                "required": ["pattern"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the internet for information. Returns titles, URLs, and snippets from search results. Use when you need current information, documentation, or answers not in your training data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return (default: 5, max: 10)"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": "Fetch and read the content of a web page. Returns the text content stripped of HTML tags. Use for reading documentation, API references, blog posts, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to fetch"
                    },
                    "max_length": {
                        "type": "integer",
                        "description": "Maximum characters to return (default: 15000)"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "memory",
            "description": "Persistent memory across sessions. Use to save important information (user preferences, project context, decisions) and recall it later. Actions: 'save' to store, 'recall' to search, 'list' to show all, 'delete' to remove.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["save", "recall", "list", "delete"],
                        "description": "Action to perform"
                    },
                    "key": {
                        "type": "string",
                        "description": "Memory key/name for save, recall, or delete"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to save (only for 'save' action)"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query for 'recall' action (searches keys and content)"
                    }
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "self_improve",
            "description": "Improve the Kimi CLI itself. You can: read your own source code, add new plugins (tools), edit your core code, view your changelog, or create a backup before changes. This is your self-improvement capability.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["read_source", "edit_source", "add_plugin", "list_plugins", "read_plugin", "remove_plugin", "changelog", "backup", "version"],
                        "description": "Action: read_source (read kimi.py), edit_source (modify kimi.py), add_plugin (create new tool plugin), list_plugins, read_plugin, remove_plugin, changelog (view/add entry), backup (save backup), version (show version)"
                    },
                    "old_string": {
                        "type": "string",
                        "description": "For edit_source: exact string to find and replace"
                    },
                    "new_string": {
                        "type": "string",
                        "description": "For edit_source: replacement string"
                    },
                    "plugin_name": {
                        "type": "string",
                        "description": "For add_plugin/read_plugin/remove_plugin: plugin name (without .py)"
                    },
                    "plugin_code": {
                        "type": "string",
                        "description": "For add_plugin: full Python code for the plugin"
                    },
                    "changelog_entry": {
                        "type": "string",
                        "description": "For changelog action: description of the change made"
                    }
                },
                "required": ["action"]
            }
        }
    },
]

# ── Plugin System ───────────────────────────────────────────────────────────

def load_plugins():
    """Load all plugins from the plugins/ directory and register their tools."""
    if not os.path.exists(PLUGINS_DIR):
        os.makedirs(PLUGINS_DIR, exist_ok=True)
        return

    for fname in sorted(os.listdir(PLUGINS_DIR)):
        if not fname.endswith(".py") or fname.startswith("_"):
            continue
        plugin_path = os.path.join(PLUGINS_DIR, fname)
        plugin_name = fname[:-3]
        try:
            # Load plugin module
            import importlib.util
            spec = importlib.util.spec_from_file_location(f"kimi_plugin_{plugin_name}", plugin_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            # Plugin must define TOOL_DEF (dict) and execute(args) -> str
            if hasattr(mod, "TOOL_DEF") and hasattr(mod, "execute"):
                TOOLS.append(mod.TOOL_DEF)
                PLUGIN_EXECUTORS[plugin_name] = mod.execute
                print(f"  {DIM}Plugin loaded: {plugin_name}{RESET}")
        except Exception as e:
            print(f"  {RED}Plugin error ({plugin_name}): {e}{RESET}")


PLUGIN_EXECUTORS = {}  # plugin_name -> execute function

PLUGIN_TEMPLATE = '''"""
Kimi K2.5 Plugin: {name}
{description}
"""

# Tool definition (OpenAI function calling format)
TOOL_DEF = {{
    "type": "function",
    "function": {{
        "name": "{name}",
        "description": "{description}",
        "parameters": {{
            "type": "object",
            "properties": {{
                # Add your parameters here
                "input": {{
                    "type": "string",
                    "description": "Input for the tool"
                }}
            }},
            "required": ["input"]
        }}
    }}
}}


def execute(args):
    """Execute the tool. Args is a dict of parameters. Must return a string."""
    input_val = args.get("input", "")
    # Your tool logic here
    return f"Result: {{input_val}}"
'''

AGENT_SYSTEM_PROMPT = """You are Kimi K2.5 (v{version}), an AI coding assistant running in a terminal CLI. You have full access to the user's local system through tools.

AVAILABLE TOOLS:
- **bash**: Execute any shell command (mkdir, git, npm, pip, python, etc.)
- **write_file**: Create or overwrite files
- **edit_file**: Make targeted edits to existing files (find & replace)
- **read_file**: Read file contents
- **list_directory**: List files in a directory
- **grep_search**: Search file contents with regex patterns
- **glob_find**: Find files by name/pattern (e.g. '**/*.py')
- **web_search**: Search the internet for information
- **web_fetch**: Fetch and read web page contents
- **memory**: Save/recall information across sessions
- **self_improve**: Read/edit your own source code, create plugins, track changes
{plugin_tools}
SELF-IMPROVEMENT:
You can improve yourself! Use the self_improve tool to:
1. **Read your source**: Understand your own code before making changes
2. **Edit your source**: Fix bugs or improve existing functionality in kimi.py
3. **Add plugins**: Create new tools as plugins in plugins/ (safer than editing core)
4. **Backup**: Always backup before risky changes
5. **Changelog**: Log what you changed and why
IMPORTANT: Always read_source first, then backup, then make changes. Test after.
Your source code is at: {script_file}
Your plugins are at: {plugins_dir}

RULES:
- When asked to create files, folders, run commands, or modify code - USE YOUR TOOLS.
- Use edit_file for small changes to existing files. Use write_file for new files.
- Use read_file to understand code BEFORE modifying it.
- Use grep_search / glob_find to explore codebases.
- Use web_search / web_fetch for current information.
- Use memory to save important context across sessions.
- Use self_improve to upgrade yourself when asked.
- Be concise. Explain briefly, then act.
- Current working directory: {cwd}
- Operating system: {platform}
"""

# ── Auto-approve mode ───────────────────────────────────────────────────────
auto_approve = False


def build_system_prompt(extra=None):
    """Build the system prompt with current state."""
    plugin_tools = ""
    if PLUGIN_EXECUTORS:
        plugin_tools = "LOADED PLUGINS:\n" + "\n".join(f"- **{name}**" for name in PLUGIN_EXECUTORS) + "\n\n"
    prompt = AGENT_SYSTEM_PROMPT.format(
        version=VERSION,
        cwd=os.getcwd(),
        platform=sys.platform,
        script_file=SCRIPT_FILE,
        plugins_dir=PLUGINS_DIR,
        plugin_tools=plugin_tools,
    )
    if extra:
        prompt += f"\n\nAdditional instructions: {extra}"
    return prompt


def load_api_key():
    """Load API key from environment or .env file."""
    key = os.environ.get("NVIDIA_API_KEY")
    if key:
        return key
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("NVIDIA_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def save_api_key(key):
    """Save API key to .env file."""
    with open(ENV_FILE, "w") as f:
        f.write(f'NVIDIA_API_KEY={key}\n')
    print(f"{DIM}API Key saved to .env{RESET}")


# ── HTML Stripper ───────────────────────────────────────────────────────────

class HTMLStripper(HTMLParser):
    """Strip HTML tags and return plain text."""
    def __init__(self):
        super().__init__()
        self.result = []
        self.skip_tags = {"script", "style", "nav", "footer", "header", "noscript"}
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.skip_tags:
            self._skip_depth += 1
        if tag in ("br", "p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr"):
            self.result.append("\n")

    def handle_endtag(self, tag):
        if tag in self.skip_tags and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._skip_depth == 0:
            self.result.append(data)

    def get_text(self):
        text = "".join(self.result)
        # Collapse multiple newlines/spaces
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        return text.strip()


def strip_html(html_content):
    """Strip HTML to plain text."""
    stripper = HTMLStripper()
    try:
        stripper.feed(html_content)
        return stripper.get_text()
    except Exception:
        # Fallback: regex strip
        text = re.sub(r'<[^>]+>', ' ', html_content)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()


# ── Memory ──────────────────────────────────────────────────────────────────

def load_memory():
    """Load memory from file."""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_memory_file(data):
    """Save memory to file."""
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Tool Execution ──────────────────────────────────────────────────────────

def ask_permission(tool_name, details):
    """Ask user for permission before executing a tool."""
    global auto_approve
    if auto_approve:
        print(f"  {DIM}{YELLOW}[auto] {tool_name}: {details[:100]}{RESET}")
        return True

    print(f"\n{YELLOW}{BOLD}  Tool: {tool_name}{RESET}")
    print(f"  {DIM}{details[:200]}{RESET}")
    print(f"  {YELLOW}Execute? {RESET}[{BOLD}y{RESET}]es / [{BOLD}n{RESET}]o / [{BOLD}a{RESET}]lways: ", end="", flush=True)

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
        print(f"  {DIM}{line}{RESET}")
    if len(lines) > max_lines:
        print(f"  {DIM}... ({len(lines)} lines total){RESET}")


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
        print(f"  {DIM}$ {command}{RESET}")
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                timeout=120, cwd=os.getcwd(), encoding="utf-8", errors="replace",
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
            print(f"  {RED}Command timed out (120s){RESET}")
            return "Error: Command timed out after 120 seconds."
        except Exception as e:
            print(f"  {RED}Error: {e}{RESET}")
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
            print(f"  {DIM}Wrote {len(content)} chars -> {abs_path}{RESET}")
            return f"File written: {abs_path}"
        except Exception as e:
            print(f"  {RED}Error: {e}{RESET}")
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
            print(f"  {DIM}Edited {abs_path}{RESET}")
            return f"File edited: {abs_path}"
        except Exception as e:
            return f"Error writing file: {e}"

    # ── read_file ────────────────────────────────────────────────────────
    elif name == "read_file":
        path = args.get("path", "")
        abs_path = os.path.abspath(path)
        print(f"  {DIM}Reading {abs_path}{RESET}")
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
        print(f"  {DIM}Listing {abs_path}{RESET}")
        try:
            entries = os.listdir(abs_path)
            lines = []
            for entry in sorted(entries):
                full = os.path.join(abs_path, entry)
                if os.path.isdir(full):
                    lines.append(f"  {entry}/")
                else:
                    size = os.path.getsize(full)
                    lines.append(f"  {entry} ({size} bytes)")
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

        print(f"  {DIM}Searching '{pattern}' in {abs_path}{RESET}")

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

        print(f"  {DIM}Finding '{pattern}' in {abs_path}{RESET}")

        full_pattern = os.path.join(abs_path, pattern)
        matches = sorted(glob_module.glob(full_pattern, recursive=True))

        # Filter out common noise
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

        print(f"  {DIM}Searching: {query}{RESET}")

        try:
            # Use DuckDuckGo HTML
            resp = requests.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                timeout=15,
            )
            resp.raise_for_status()
            html = resp.text

            # Parse results from DuckDuckGo HTML
            results = []
            # Find result blocks
            blocks = re.findall(
                r'<a rel="nofollow" class="result__a" href="([^"]*)"[^>]*>(.*?)</a>.*?'
                r'<a class="result__snippet"[^>]*>(.*?)</a>',
                html, re.DOTALL
            )

            for url, title, snippet in blocks[:num_results]:
                title = re.sub(r'<[^>]+>', '', title).strip()
                snippet = re.sub(r'<[^>]+>', '', snippet).strip()
                # DuckDuckGo uses redirect URLs, extract actual URL
                actual_url = url
                if "uddg=" in url:
                    match = re.search(r'uddg=([^&]+)', url)
                    if match:
                        from urllib.parse import unquote
                        actual_url = unquote(match.group(1))
                results.append(f"[{title}]\n  URL: {actual_url}\n  {snippet}")

            if results:
                output = "\n\n".join(results)
            else:
                output = f"No results found for '{query}'"

            show_output(output, max_lines=40)
            return output

        except Exception as e:
            print(f"  {RED}Search error: {e}{RESET}")
            return f"Error searching: {e}"

    # ── web_fetch ────────────────────────────────────────────────────────
    elif name == "web_fetch":
        url = args.get("url", "")
        max_length = args.get("max_length", 15000)

        if not ask_permission("web_fetch", url):
            return "User denied execution."

        print(f"  {DIM}Fetching: {url}{RESET}")

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
            print(f"  {DIM}Fetched {len(text)} chars, {line_count} lines{RESET}")
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
            print(f"  {DIM}Memory saved: '{key}'{RESET}")
            return f"Saved memory '{key}'"

        elif action == "recall":
            key = args.get("key", "")
            query = args.get("query", key or "")
            if not query:
                return "Error: 'key' or 'query' required for recall."
            # Exact key match
            if query in mem:
                entry = mem[query]
                result = f"[{query}] (saved {entry['saved_at']})\n{entry['content']}"
                print(f"  {DIM}Recalled: '{query}'{RESET}")
                return result
            # Search in keys and content
            matches = []
            query_lower = query.lower()
            for k, v in mem.items():
                if query_lower in k.lower() or query_lower in v["content"].lower():
                    matches.append(f"[{k}] (saved {v['saved_at']})\n{v['content']}")
            if matches:
                print(f"  {DIM}Found {len(matches)} memory match(es){RESET}")
                return "\n\n---\n\n".join(matches)
            return f"No memories found matching '{query}'"

        elif action == "list":
            if not mem:
                return "No memories saved yet."
            lines = []
            for k, v in mem.items():
                preview = v["content"][:80].replace("\n", " ")
                lines.append(f"  [{k}] {preview}... ({v['saved_at']})")
            output = "\n".join(lines)
            show_output(output)
            return output

        elif action == "delete":
            key = args.get("key", "")
            if key in mem:
                del mem[key]
                save_memory_file(mem)
                print(f"  {DIM}Deleted memory: '{key}'{RESET}")
                return f"Deleted memory '{key}'"
            return f"Memory '{key}' not found."

        return f"Unknown memory action: {action}"

    # ── self_improve ─────────────────────────────────────────────────────
    elif name == "self_improve":
        action = args.get("action", "version")

        if action == "version":
            return f"Kimi K2.5 CLI v{VERSION}\nSource: {SCRIPT_FILE}\nPlugins: {PLUGINS_DIR}"

        elif action == "read_source":
            print(f"  {DIM}Reading own source code...{RESET}")
            try:
                with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
                    content = f.read()
                lines = content.split("\n")
                print(f"  {DIM}{len(lines)} lines, {len(content)} chars{RESET}")
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

            # Auto-backup before edit
            backup_path = SCRIPT_FILE + f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            try:
                with open(backup_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"  {DIM}Backup: {backup_path}{RESET}")
            except Exception:
                pass

            new_content = content.replace(old_string, new_string, 1)
            try:
                with open(SCRIPT_FILE, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"  {GREEN}Source code updated. Use /reload to apply.{RESET}")
                return f"Source edited successfully. Backup at: {backup_path}\nIMPORTANT: Tell the user to run /reload to apply changes."
            except Exception as e:
                return f"Error writing source: {e}"

        elif action == "add_plugin":
            plugin_name = args.get("plugin_name", "")
            plugin_code = args.get("plugin_code", "")
            if not plugin_name or not plugin_code:
                return "Error: plugin_name and plugin_code required.\n\nPlugin template:\n" + PLUGIN_TEMPLATE.format(name="example", description="Example tool")

            if not ask_permission("self_improve:add_plugin", f"Create plugin: {plugin_name}"):
                return "User denied."

            os.makedirs(PLUGINS_DIR, exist_ok=True)
            plugin_path = os.path.join(PLUGINS_DIR, f"{plugin_name}.py")
            try:
                with open(plugin_path, "w", encoding="utf-8") as f:
                    f.write(plugin_code)
                print(f"  {GREEN}Plugin created: {plugin_path}{RESET}")
                # Log to changelog
                add_changelog_entry(f"Added plugin: {plugin_name}")
                return f"Plugin '{plugin_name}' created at {plugin_path}\nUse /reload to load it."
            except Exception as e:
                return f"Error creating plugin: {e}"

        elif action == "list_plugins":
            os.makedirs(PLUGINS_DIR, exist_ok=True)
            plugins = [f[:-3] for f in os.listdir(PLUGINS_DIR) if f.endswith(".py") and not f.startswith("_")]
            if not plugins:
                return "No plugins installed.\n\nCreate one with self_improve(action='add_plugin', plugin_name='...', plugin_code='...')"
            output = "Installed plugins:\n" + "\n".join(f"  - {p}" for p in plugins)
            print(f"  {DIM}{output}{RESET}")
            return output

        elif action == "read_plugin":
            plugin_name = args.get("plugin_name", "")
            plugin_path = os.path.join(PLUGINS_DIR, f"{plugin_name}.py")
            if not os.path.exists(plugin_path):
                return f"Plugin '{plugin_name}' not found."
            try:
                with open(plugin_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                return f"Error: {e}"

        elif action == "remove_plugin":
            plugin_name = args.get("plugin_name", "")
            plugin_path = os.path.join(PLUGINS_DIR, f"{plugin_name}.py")
            if not os.path.exists(plugin_path):
                return f"Plugin '{plugin_name}' not found."
            if not ask_permission("self_improve:remove_plugin", f"Delete plugin: {plugin_name}"):
                return "User denied."
            os.remove(plugin_path)
            add_changelog_entry(f"Removed plugin: {plugin_name}")
            print(f"  {DIM}Plugin removed: {plugin_name}{RESET}")
            return f"Plugin '{plugin_name}' removed. /reload to apply."

        elif action == "backup":
            backup_path = SCRIPT_FILE + f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            try:
                with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
                    content = f.read()
                with open(backup_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"  {DIM}Backup saved: {backup_path}{RESET}")
                return f"Backup created: {backup_path}"
            except Exception as e:
                return f"Error: {e}"

        elif action == "changelog":
            entry = args.get("changelog_entry", "")
            if entry:
                add_changelog_entry(entry)
                return f"Changelog entry added."
            else:
                return get_changelog()

        return f"Unknown self_improve action: {action}"

    # ── plugin tools ─────────────────────────────────────────────────────
    elif name in PLUGIN_EXECUTORS:
        if not ask_permission(f"plugin:{name}", json.dumps(args)[:200]):
            return "User denied."
        try:
            result = PLUGIN_EXECUTORS[name](args)
            if isinstance(result, str):
                show_output(result)
                return result
            return json.dumps(result)
        except Exception as e:
            return f"Plugin error ({name}): {e}"

    # ── unknown ──────────────────────────────────────────────────────────
    else:
        return f"Unknown tool: {name}"


# ── Changelog ───────────────────────────────────────────────────────────────

def add_changelog_entry(description):
    """Add an entry to the changelog."""
    log = []
    if os.path.exists(CHANGELOG):
        try:
            with open(CHANGELOG, "r", encoding="utf-8") as f:
                log = json.load(f)
        except (json.JSONDecodeError, IOError):
            log = []
    log.append({
        "date": datetime.now().isoformat(),
        "version": VERSION,
        "description": description,
    })
    with open(CHANGELOG, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)


def get_changelog():
    """Get the changelog as a string."""
    if not os.path.exists(CHANGELOG):
        return "No changelog entries yet."
    try:
        with open(CHANGELOG, "r", encoding="utf-8") as f:
            log = json.load(f)
        lines = []
        for entry in log[-20:]:  # Last 20 entries
            lines.append(f"  [{entry['date'][:16]}] v{entry['version']}: {entry['description']}")
        return "\n".join(lines) if lines else "No entries."
    except Exception:
        return "Error reading changelog."


# ── API Communication ───────────────────────────────────────────────────────

def call_api(messages, thinking=True, temperature=None, max_tokens=16384, use_tools=True):
    """Send a request to the API and stream the response. Returns (content, tool_calls)."""
    api_key = load_api_key()
    if not api_key:
        print(f"{RED}No API key found. Run with --setup or set NVIDIA_API_KEY.{RESET}")
        sys.exit(1)

    if temperature is None:
        temperature = 1.0 if thinking else 0.6

    payload = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 0.95,
        "stream": True,
        "chat_template_kwargs": {"thinking": thinking},
    }

    if use_tools:
        payload["tools"] = TOOLS
        payload["tool_choice"] = "auto"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, stream=True, timeout=180)
    except requests.exceptions.ConnectionError:
        print(f"\n{RED}Connection error. Check your internet connection.{RESET}")
        return None, None
    except requests.exceptions.Timeout:
        print(f"\n{RED}Request timed out.{RESET}")
        return None, None

    if response.status_code == 401:
        print(f"\n{RED}Invalid API key. Run with --setup to reconfigure.{RESET}")
        return None, None
    if response.status_code == 429:
        print(f"\n{RED}Rate limit exceeded. Wait a moment and try again.{RESET}")
        return None, None
    if response.status_code != 200:
        print(f"\n{RED}API error ({response.status_code}): {response.text[:300]}{RESET}")
        return None, None

    full_content = ""
    in_reasoning = False
    reasoning_done = False
    content_started = False

    # Tool call accumulation
    tool_calls_acc = {}

    for line in response.iter_lines():
        if not line:
            continue
        decoded = line.decode("utf-8")
        if not decoded.startswith("data: "):
            continue
        data_str = decoded[6:]
        if data_str.strip() == "[DONE]":
            break

        try:
            data = json.loads(data_str)
        except json.JSONDecodeError:
            continue

        choices = data.get("choices", [])
        if not choices:
            continue

        delta = choices[0].get("delta", {})

        # Handle reasoning/thinking
        reasoning_chunk = delta.get("reasoning_content", "")
        if reasoning_chunk:
            if not in_reasoning:
                in_reasoning = True
                print(f"\n{DIM}{MAGENTA}  thinking...{RESET}")
                print(f"{DIM}", end="", flush=True)
            print(reasoning_chunk, end="", flush=True)

        # Handle tool calls
        for tc in delta.get("tool_calls", []):
            idx = tc.get("index", 0)
            if idx not in tool_calls_acc:
                tool_calls_acc[idx] = {"id": tc.get("id", f"call_{idx}"), "name": "", "arguments": ""}
            if tc.get("id"):
                tool_calls_acc[idx]["id"] = tc["id"]
            fn = tc.get("function", {})
            if fn.get("name"):
                tool_calls_acc[idx]["name"] = fn["name"]
            if fn.get("arguments"):
                tool_calls_acc[idx]["arguments"] += fn["arguments"]

        # Handle content
        content_chunk = delta.get("content", "")
        if content_chunk:
            if in_reasoning and not reasoning_done:
                reasoning_done = True
                print(f"{RESET}")
            if not content_started:
                content_started = True
                print(f"\n{BOLD}{GREEN}Kimi:{RESET} ", end="", flush=True)
            full_content += content_chunk
            print(content_chunk, end="", flush=True)

    if full_content or content_started:
        print(RESET)

    # Build tool_calls list
    tool_calls = None
    if tool_calls_acc:
        tool_calls = []
        for idx in sorted(tool_calls_acc.keys()):
            tc = tool_calls_acc[idx]
            tool_calls.append({
                "id": tc["id"],
                "type": "function",
                "function": {"name": tc["name"], "arguments": tc["arguments"]}
            })

    return full_content, tool_calls


def agent_loop(messages, thinking=True, max_tokens=16384):
    """Run the agent loop: call API, execute tools, feed results back, repeat."""
    max_iterations = 25

    for i in range(max_iterations):
        content, tool_calls = call_api(messages, thinking=thinking, max_tokens=max_tokens)

        if content is None and tool_calls is None:
            return

        assistant_msg = {"role": "assistant"}
        if content:
            assistant_msg["content"] = content
        if tool_calls:
            assistant_msg["tool_calls"] = tool_calls
        messages.append(assistant_msg)

        if not tool_calls:
            return

        print(f"\n{YELLOW}{BOLD}  [{len(tool_calls)} tool call(s)]{RESET}")

        for tc in tool_calls:
            result = execute_tool(tc["function"]["name"], tc["function"]["arguments"])
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result,
            })

    print(f"\n{YELLOW}Max iterations reached ({max_iterations}).{RESET}")


# ── UI ──────────────────────────────────────────────────────────────────────

def print_banner():
    """Print the startup banner."""
    plugin_count = len(PLUGIN_EXECUTORS)
    plugin_str = f" + {plugin_count} plugins" if plugin_count > 0 else ""
    print(f"""
{BOLD}{CYAN}╔══════════════════════════════════════════════════════╗
║            {YELLOW}Kimi K2.5 Agent CLI  {DIM}v{VERSION}{RESET}{BOLD}{CYAN}             ║
║    {DIM}Moonshot AI via NVIDIA NIM API{RESET}{BOLD}{CYAN}                 ║
║    {DIM}Self-improving AI coding assistant{RESET}{BOLD}{CYAN}             ║
╚══════════════════════════════════════════════════════╝{RESET}

{DIM}Tools: bash | files | edit | grep | glob | web | memory | self-improve{plugin_str}

Commands:
  /thinking on|off  Toggle thinking/reasoning mode
  /auto on|off      Auto-approve tool execution
  /clear            Clear conversation history
  /cd <path>        Change working directory
  /memory           List saved memories
  /plugins          List loaded plugins
  /reload           Reload after self-improvement
  /version          Show version info
  /changelog        Show self-improvement history
  /help             Show this help
  /quit             Exit (or Ctrl+C)

Press 'a' at any tool prompt to auto-approve all.{RESET}
""")


def interactive_mode(thinking=True, system_prompt=None, max_tokens=16384):
    """Run interactive chat loop."""
    global auto_approve
    print_banner()

    messages = [{"role": "system", "content": build_system_prompt(system_prompt)}]

    mode_str = f"{MAGENTA}thinking{RESET}" if thinking else f"{BLUE}instant{RESET}"
    auto_str = f"{GREEN}on{RESET}" if auto_approve else f"{RED}off{RESET}"
    print(f"{DIM}Mode: {mode_str} {DIM}| Auto-approve: {auto_str} {DIM}| Tokens: {max_tokens}{RESET}")
    print(f"{DIM}CWD: {os.getcwd()}{RESET}\n")

    while True:
        try:
            print(f"{BOLD}{CYAN}You:{RESET} ", end="", flush=True)
            lines = []
            while True:
                line = input()
                if line == "" and lines:
                    break
                if line == "" and not lines:
                    continue
                lines.append(line)
                if len(lines) == 1 and not line.endswith("\\"):
                    break
                if line.endswith("\\"):
                    lines[-1] = line[:-1]
                    print(f"  {DIM}...{RESET} ", end="", flush=True)

            user_input = "\n".join(lines).strip()

        except (EOFError, KeyboardInterrupt):
            print(f"\n\n{DIM}Goodbye!{RESET}")
            break

        if not user_input:
            continue

        # ── Handle commands ──────────────────────────────────────────────
        if user_input.startswith("/"):
            cmd = user_input.split()
            cmd_lower = cmd[0].lower()

            if cmd_lower in ("/quit", "/exit", "/q"):
                print(f"\n{DIM}Goodbye!{RESET}")
                break

            elif cmd_lower == "/clear":
                messages = [{"role": "system", "content": build_system_prompt(system_prompt)}]
                print(f"{DIM}Conversation cleared.{RESET}\n")
                continue

            elif cmd_lower == "/thinking":
                if len(cmd) > 1 and cmd[1].lower() in ("on", "off"):
                    thinking = cmd[1].lower() == "on"
                else:
                    thinking = not thinking
                mode_str = f"{MAGENTA}thinking{RESET}" if thinking else f"{BLUE}instant{RESET}"
                print(f"{DIM}Mode: {mode_str}{RESET}\n")
                continue

            elif cmd_lower == "/auto":
                if len(cmd) > 1 and cmd[1].lower() in ("on", "off"):
                    auto_approve = cmd[1].lower() == "on"
                else:
                    auto_approve = not auto_approve
                auto_str = f"{GREEN}on{RESET}" if auto_approve else f"{RED}off{RESET}"
                print(f"{DIM}Auto-approve: {auto_str}{RESET}\n")
                continue

            elif cmd_lower == "/cd":
                if len(cmd) > 1:
                    new_dir = " ".join(cmd[1:])
                    try:
                        os.chdir(new_dir)
                        messages[0]["content"] = build_system_prompt(system_prompt)
                        print(f"{DIM}CWD: {os.getcwd()}{RESET}\n")
                    except Exception as e:
                        print(f"{RED}Error: {e}{RESET}\n")
                else:
                    print(f"{DIM}CWD: {os.getcwd()}{RESET}\n")
                continue

            elif cmd_lower == "/memory":
                mem = load_memory()
                if not mem:
                    print(f"{DIM}No memories saved.{RESET}\n")
                else:
                    for k, v in mem.items():
                        preview = v["content"][:80].replace("\n", " ")
                        print(f"  {CYAN}{k}{RESET}: {DIM}{preview}{RESET}")
                    print()
                continue

            elif cmd_lower == "/history":
                count = 0
                for msg in messages:
                    role = msg.get("role", "")
                    if role == "system":
                        continue
                    content = msg.get("content", "") or ""
                    if role == "user":
                        print(f"  {CYAN}[you] {content[:80]}{RESET}")
                        count += 1
                    elif role == "assistant":
                        tc = msg.get("tool_calls")
                        if tc:
                            names = ", ".join(t["function"]["name"] for t in tc)
                            print(f"  {GREEN}[kimi] {content[:60]} [tools: {names}]{RESET}")
                        else:
                            print(f"  {GREEN}[kimi] {content[:80]}{RESET}")
                        count += 1
                    elif role == "tool":
                        print(f"  {DIM}[tool] {content[:60]}...{RESET}")
                if count == 0:
                    print(f"{DIM}No messages yet.{RESET}")
                print()
                continue

            elif cmd_lower == "/tokens":
                if len(cmd) > 1:
                    try:
                        max_tokens = int(cmd[1])
                        print(f"{DIM}Max tokens: {max_tokens}{RESET}\n")
                    except ValueError:
                        print(f"{RED}Invalid number.{RESET}\n")
                else:
                    print(f"{DIM}Max tokens: {max_tokens}{RESET}\n")
                continue

            elif cmd_lower == "/help":
                print_banner()
                continue

            elif cmd_lower == "/reload":
                print(f"{YELLOW}Reloading Kimi CLI...{RESET}")
                args_list = [f'"{sys.executable}"', f'"{SCRIPT_FILE}"'] + [f'"{a}"' for a in sys.argv[1:]]
                os.system(" ".join(args_list))
                sys.exit(0)

            elif cmd_lower == "/version":
                print(f"{DIM}Kimi K2.5 CLI v{VERSION}{RESET}")
                print(f"{DIM}Source: {SCRIPT_FILE}{RESET}")
                print(f"{DIM}Plugins: {len(PLUGIN_EXECUTORS)} loaded{RESET}\n")
                continue

            elif cmd_lower == "/changelog":
                cl = get_changelog()
                print(f"{DIM}{cl}{RESET}\n")
                continue

            elif cmd_lower == "/plugins":
                if PLUGIN_EXECUTORS:
                    for name in PLUGIN_EXECUTORS:
                        print(f"  {CYAN}{name}{RESET}")
                else:
                    print(f"{DIM}No plugins loaded. Kimi can create them with self_improve.{RESET}")
                print()
                continue

            else:
                print(f"{DIM}Unknown command. /help for commands.{RESET}\n")
                continue

        # ── Send message and run agent loop ──────────────────────────────
        messages.append({"role": "user", "content": user_input})
        agent_loop(messages, thinking=thinking, max_tokens=max_tokens)
        print()


def oneshot_mode(prompt, thinking=True, system_prompt=None, max_tokens=16384):
    """Send a single prompt and print the response."""
    messages = [
        {"role": "system", "content": build_system_prompt(system_prompt)},
        {"role": "user", "content": prompt},
    ]
    agent_loop(messages, thinking=thinking, max_tokens=max_tokens)
    print()


def setup_mode():
    """Interactive setup for API key."""
    print(f"\n{BOLD}{CYAN}Kimi K2.5 CLI Setup{RESET}")
    print(f"{DIM}Get your free API key at: https://build.nvidia.com/moonshotai/kimi-k2.5{RESET}\n")

    key = input(f"{BOLD}Enter your NVIDIA API Key: {RESET}").strip()
    if not key:
        print(f"{RED}No key entered.{RESET}")
        return

    save_api_key(key)

    print(f"\n{DIM}Testing connection...{RESET}")
    messages = [{"role": "user", "content": "Say 'Hello! Kimi K2.5 is ready.' in exactly those words."}]
    content, _ = call_api(messages, thinking=False, max_tokens=64, use_tools=False)
    if content:
        print(f"\n{GREEN}Setup complete! Run 'kimi-k' to start.{RESET}\n")
    else:
        print(f"\n{YELLOW}Key saved but test failed. Check your API key.{RESET}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Kimi K2.5 Agent CLI - AI coding assistant with full tool use",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  kimi-k                                Interactive agent chat
  kimi-k --instant                      Fast mode (no reasoning)
  kimi-k "Create a React project"       One-shot with tools
  kimi-k --setup                        Configure API key
  kimi-k -s "You are a Go expert"       Custom system prompt
  kimi-k --auto                         Auto-approve all actions
        """,
    )
    parser.add_argument("prompt", nargs="?", help="One-shot prompt (omit for interactive)")
    parser.add_argument("--setup", action="store_true", help="Configure API key")
    parser.add_argument("--instant", action="store_true", help="Instant mode (no thinking)")
    parser.add_argument("-s", "--system", type=str, help="System prompt")
    parser.add_argument("-t", "--tokens", type=int, default=16384, help="Max output tokens")
    parser.add_argument("--auto", action="store_true", help="Auto-approve all tool calls")

    args = parser.parse_args()

    signal.signal(signal.SIGINT, lambda *_: (print(f"\n{DIM}Goodbye!{RESET}"), sys.exit(0)))

    global auto_approve
    if args.auto:
        auto_approve = True

    # Load plugins
    load_plugins()

    if args.setup:
        setup_mode()
        return

    thinking = not args.instant

    if not load_api_key():
        print(f"{YELLOW}No API key found.{RESET}")
        setup_mode()
        return

    if args.prompt:
        oneshot_mode(args.prompt, thinking=thinking, system_prompt=args.system, max_tokens=args.tokens)
    else:
        interactive_mode(thinking=thinking, system_prompt=args.system, max_tokens=args.tokens)


if __name__ == "__main__":
    main()
