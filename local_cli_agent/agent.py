# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Steffen Schwabe
import json
import re

from local_cli_agent.constants import RESET, BOLD, DIM, YELLOW
from local_cli_agent.api import call_api
from local_cli_agent.executor import execute_tool


# ── Markdown Tool Extractor ───────────────────────────────────────────────────
# Reasoning models (gemma-reasoning, qwen-thinking, etc.) sometimes output
# code blocks instead of proper JSON tool calls. This extracts them.

_FILE_EXTS = re.compile(
    r'\b([\w\-]+\.(?:html?|css|js|ts|jsx|tsx|py|json|yaml|yml|md|txt|sh|bat|ps1|xml|svg))\b'
)
_CODE_BLOCK = re.compile(r'```(\w*)\n(.*?)```', re.DOTALL)

_LANG_DEFAULTS = {
    'html': 'index.html', 'htm': 'index.html',
    'css':  'style.css',
    'javascript': 'script.js', 'js': 'script.js',
    'jsx':  'app.jsx',
    'typescript': 'main.ts',   'ts': 'main.ts',
    'tsx':  'app.tsx',
    'python': 'main.py',       'py': 'main.py',
    'json': 'data.json',
    'yaml': 'config.yaml',     'yml': 'config.yml',
    'markdown': 'README.md',   'md': 'README.md',
    'xml':  'data.xml',
    'svg':  'image.svg',
    'bash': None, 'sh': None, 'shell': None, 'cmd': None, 'powershell': None, 'ps1': None,
}


def _extract_tool_calls_from_markdown(content: str) -> list:
    """
    Parse markdown content for fenced code blocks and synthesize tool calls.
    Used as fallback when the model outputs markdown instead of JSON tool calls.
    - bash/sh blocks  → bash tool
    - code file blocks → write_file tool (filename from context or default)
    """
    tool_calls = []

    for i, m in enumerate(_CODE_BLOCK.finditer(content)):
        lang = m.group(1).lower().strip()
        code = m.group(2).strip()

        if not code:
            continue
        if lang not in _LANG_DEFAULTS:
            continue

        if lang in ('bash', 'sh', 'shell', 'cmd', 'powershell', 'ps1'):
            # Take first meaningful (non-comment) line as the command
            cmd = next(
                (line for line in code.splitlines()
                 if line.strip() and not line.strip().startswith('#')),
                code,
            )
            tool_calls.append({
                "id": f"md_{i}",
                "type": "function",
                "function": {
                    "name": "bash",
                    "arguments": json.dumps({"command": cmd}),
                },
            })
        else:
            # Find filename: check text before this block first, then whole content
            context_before = content[:m.start()]
            hits = _FILE_EXTS.findall(context_before)
            if not hits:
                hits = _FILE_EXTS.findall(content)
            filename = hits[-1][0] if hits else (_LANG_DEFAULTS.get(lang) or f"output.{lang}")

            tool_calls.append({
                "id": f"md_{i}",
                "type": "function",
                "function": {
                    "name": "write_file",
                    "arguments": json.dumps({"path": filename, "content": code}),
                },
            })

    return tool_calls


# ── Agent loop ────────────────────────────────────────────────────────────────
def agent_loop(messages, thinking=True, max_tokens=16384):
    """Run the agent loop: call API, execute tools, feed results back, repeat."""
    max_iterations = 25
    for i in range(max_iterations):
        content, tool_calls = call_api(messages, thinking=thinking, max_tokens=max_tokens)
        if content is None and tool_calls is None:
            return

        # ── Fallback: extract tool calls from markdown if model didn't use JSON ──
        if not tool_calls and content:
            tool_calls = _extract_tool_calls_from_markdown(content)
            if tool_calls:
                print(f"\n{DIM}[Codeblöcke erkannt – führe Tools aus]{RESET}")

        assistant_msg = {"role": "assistant"}
        if content:
            assistant_msg["content"] = content
        if tool_calls:
            assistant_msg["tool_calls"] = tool_calls
        messages.append(assistant_msg)

        if not tool_calls:
            return

        print(f"\n{YELLOW}{BOLD} [{len(tool_calls)} tool call(s)]{RESET}")
        for tc in tool_calls:
            result = execute_tool(tc["function"]["name"], tc["function"]["arguments"])
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result,
            })
        print(f"{DIM}  ↻ Verarbeite Ergebnisse...{RESET}", end="", flush=True)

    print(f"\n{YELLOW}Max iterations reached ({max_iterations}).{RESET}")