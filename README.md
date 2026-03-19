# kimi-k-cli

A self-improving AI coding assistant for your terminal, powered by [Moonshot AI's Kimi K2.5](https://build.nvidia.com/moonshotai/kimi-k2.5) via NVIDIA NIM API. Kimi-K is a standalone agent that can execute commands, edit code, search the web, and even improve its own source code.

![Python](https://img.shields.io/badge/python-3.8+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

- **Interactive terminal chat** - Just type `kimi-k` and start talking
- **Full tool use** - Bash commands, file read/write/edit, directory operations
- **Code search** - Grep and glob across your codebase
- **Web access** - Search the internet and fetch web pages
- **Persistent memory** - Remembers things across sessions
- **Self-improvement** - Kimi can read/edit its own source code and create plugins
- **Plugin system** - Extend with custom tools that auto-load
- **Thinking mode** - Toggle reasoning traces on/off
- **Safety first** - Asks permission before executing actions

## Quick Start

### 1. Prerequisites

- Python 3.8+
- `requests` library (`pip install requests`)
- Free NVIDIA API key (see below)

### 2. Get your free NVIDIA API Key

1. Go to [build.nvidia.com/moonshotai/kimi-k2.5](https://build.nvidia.com/moonshotai/kimi-k2.5)
2. Click **Login** (top right) and create a free NVIDIA account or sign in
3. Once logged in, click the **View Code** button (top right)
4. In the modal that opens, click **Generate API Key**
5. Copy the key (starts with `nvapi-...`)

The free tier is sufficient for development and personal use.

### 3. Install

```bash
git clone https://github.com/suebi76/kimi-k-cli.git
cd kimi-k-cli
pip install requests
python kimi.py --setup
```

The setup wizard will ask for your API key and test the connection.

### 3. Add to PATH (optional)

To run `kimi-k` from anywhere:

**Linux/macOS:**
```bash
ln -s $(pwd)/kimi.py ~/.local/bin/kimi-k
chmod +x kimi.py
```

**Windows (Git Bash):**
```bash
# Copy to Python Scripts (already on PATH)
cp kimi-k-launch.sh "$(dirname $(which python))/Scripts/kimi-k"
```

Or create a batch file in a PATH directory:
```batch
@echo off
python "C:\path\to\kimi-k-cli\kimi.py" %*
```

## Usage

```bash
# Interactive chat (default: thinking mode)
kimi-k

# Fast mode without reasoning
kimi-k --instant

# One-shot question
kimi-k "Create a Python Flask API with user authentication"

# With custom system prompt
kimi-k -s "You are a Go expert"

# Auto-approve all tool executions
kimi-k --auto

# Configure API key
kimi-k --setup
```

## Tools (11 built-in)

| Tool | Description |
|---|---|
| `bash` | Execute any shell command |
| `write_file` | Create or overwrite files |
| `edit_file` | Find & replace in existing files |
| `read_file` | Read file contents |
| `list_directory` | List files and directories |
| `grep_search` | Search file contents with regex |
| `glob_find` | Find files by pattern |
| `web_search` | Search the internet (DuckDuckGo) |
| `web_fetch` | Fetch and read web pages |
| `memory` | Persistent key-value memory |
| `self_improve` | Read/edit own source, manage plugins |

## Slash Commands

| Command | Description |
|---|---|
| `/thinking on\|off` | Toggle thinking/reasoning mode |
| `/auto on\|off` | Auto-approve tool execution |
| `/clear` | Clear conversation history |
| `/cd <path>` | Change working directory |
| `/memory` | List saved memories |
| `/plugins` | List loaded plugins |
| `/reload` | Reload after self-improvement |
| `/version` | Show version info |
| `/changelog` | Show self-improvement history |
| `/tokens <n>` | Set max output tokens |
| `/help` | Show help |
| `/quit` | Exit |

## Self-Improvement

Kimi can improve itself. Just ask:

- *"Create a plugin that converts Markdown to HTML"*
- *"Add syntax highlighting to your code output"*
- *"Read your own code and suggest improvements"*

### Plugin System

Plugins are Python files in the `plugins/` directory. They auto-load on startup.

**Plugin structure:**
```python
"""
Kimi K2.5 Plugin: my_tool
Does something useful.
"""

TOOL_DEF = {
    "type": "function",
    "function": {
        "name": "my_tool",
        "description": "What this tool does",
        "parameters": {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input parameter"
                }
            },
            "required": ["input"]
        }
    }
}

def execute(args):
    """Execute the tool. Must return a string."""
    return f"Result: {args.get('input', '')}"
```

## How It Works

```
User Input -> Kimi K2.5 API (NVIDIA NIM) -> Tool Calls -> Execute Locally -> Feed Results Back -> Response
```

The CLI implements an **agent loop**: Kimi decides which tools to use, the CLI executes them locally, and feeds results back until Kimi has a final answer. Up to 25 iterations per turn.

## Configuration

| File | Purpose |
|---|---|
| `.env` | NVIDIA API key |
| `.kimi-memory.json` | Persistent memory (auto-created) |
| `.kimi-changelog.json` | Self-improvement log (auto-created) |
| `plugins/` | Custom tool plugins |

## API

Uses the [NVIDIA NIM API](https://build.nvidia.com/moonshotai/kimi-k2.5) (OpenAI-compatible). Free tier available for development.

- **Model**: `moonshotai/kimi-k2.5`
- **Parameters**: 1T total, 32B activated (MoE)
- **Context**: 256K tokens
- **Capabilities**: Text, image, video input; reasoning; tool use

## License

MIT
