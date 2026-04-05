# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Steffen Schwabe
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
                    "command": {"type": "string", "description": "The shell command to execute"}
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
                    "path": {"type": "string", "description": "Absolute or relative file path"},
                    "content": {"type": "string", "description": "The full content to write to the file"}
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
                    "path": {"type": "string", "description": "File path to edit"},
                    "old_string": {"type": "string", "description": "The exact string to find and replace (must be unique in the file)"},
                    "new_string": {"type": "string", "description": "The replacement string"}
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
                    "path": {"type": "string", "description": "Absolute or relative file path to read"}
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
                    "path": {"type": "string", "description": "Directory path to list (default: current directory)"}
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
                    "pattern": {"type": "string", "description": "Regex pattern to search for"},
                    "path": {"type": "string", "description": "Directory or file to search in (default: current directory)"},
                    "file_pattern": {"type": "string", "description": "Glob pattern to filter files, e.g. '*.py', '*.js', '*.ts' (default: all files)"},
                    "ignore_case": {"type": "boolean", "description": "Case insensitive search (default: false)"}
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
                    "pattern": {"type": "string", "description": "Glob pattern, e.g. '**/*.py', 'src/**/*.ts', '**/package.json'"},
                    "path": {"type": "string", "description": "Base directory to search from (default: current directory)"}
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
                    "query": {"type": "string", "description": "The search query"},
                    "num_results": {"type": "integer", "description": "Number of results to return (default: 5, max: 10)"}
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
                    "url": {"type": "string", "description": "The URL to fetch"},
                    "max_length": {"type": "integer", "description": "Maximum characters to return (default: 15000)"}
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
                    "action": {"type": "string", "enum": ["save", "recall", "list", "delete"], "description": "Action to perform"},
                    "key": {"type": "string", "description": "Memory key/name for save, recall, or delete"},
                    "content": {"type": "string", "description": "Content to save (only for 'save' action)"},
                    "query": {"type": "string", "description": "Search query for 'recall' action (searches keys and content)"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "self_improve",
            "description": "Verbessere dich selbst (Local CLI Agent). Quellcode lesen, bearbeiten, Backup erstellen oder Changelog pflegen. Syntax wird automatisch geprüft – defekter Code wird NICHT gespeichert. Backup ist Pflicht vor jeder Änderung.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["read_source", "edit_source", "changelog", "backup", "version"], "description": "Aktion: read_source (Quellcode lesen), edit_source (bearbeiten), changelog (anzeigen/hinzufügen), backup (Sicherung), version (Version + Dateiliste)"},
                    "file": {"type": "string", "description": "Dateiname im Paket, z.B. 'cli.py', 'agent.py', 'executor.py'. Standard: cli.py"},
                    "old_string": {"type": "string", "description": "Für edit_source: exakter Suchstring (muss eindeutig sein)"},
                    "new_string": {"type": "string", "description": "Für edit_source: Ersetzungsstring"},
                    "changelog_entry": {"type": "string", "description": "Für changelog: Beschreibung der Änderung"}
                },
                "required": ["action"]
            }
        }
    },
]

FORMATTING_RULES = """
FORMATTING RULES FOR TERMINAL OUTPUT:

1. NEVER use Markdown tables (syntax: | Column | Column |)
   - They render poorly in terminal output
   - Lines break, alignment is lost

2. INSTEAD use ONE of these formats:

   Option A: Unicode Box Tables (for 2-4 columns)
   ┌────────────┬────────────┬────────────┐
   │ Header 1   │ Header 2   │ Header 3   │
   ├────────────┼────────────┼────────────┤
   │ Data 1     │ Data 2     │ Data 3     │
   └────────────┴────────────┴────────────┘

   Option B: Bullet lists with arrows (for complex data)
   ► Item: Value
     └─ Detail: Explanation

   Option C: Section headers with indentation
   ─────────────────────────────────────────
   SECTION NAME
   ─────────────────────────────────────────
   • Key: Value
   • Key: Value

3. CODE BLOCKS: Always specify language
   ```python
   def example():
       pass
   ```

4. EMPHASIS: Use **bold** or `code` instead of tables for comparisons
"""