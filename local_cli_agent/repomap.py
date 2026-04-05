# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Steffen Schwabe
"""
Compact repository map for system prompt injection.

Scans Python source files in the current project directory using the
built-in ast module (zero extra dependencies). Extracts classes, their
methods, and top-level functions. Produces a short, human-readable
summary that the agent can use to navigate the codebase without reading
every file.
"""

import ast
import os
from pathlib import Path

_SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv", "env",
    "dist", "build", ".mypy_cache", ".pytest_cache", ".tox", ".eggs",
    "htmlcov", ".ruff_cache",
}
_MAX_FILES = 150   # never scan more than this many .py files
_MAX_LINES = 100   # max lines in the repo-map output


def _parse_python(path: str) -> list[str]:
    """
    Extract class names, their methods, and top-level functions from a .py file.
    Returns a list of indented strings, e.g.:
        ['  class Foo:', '    def bar()', '  def standalone()']
    """
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
        tree = ast.parse(source)
    except Exception:
        return []

    lines: list[str] = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            lines.append(f"  class {node.name}:")
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    lines.append(f"    def {item.name}()")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            lines.append(f"  def {node.name}()")

    return lines


def _is_project_root(path: Path) -> bool:
    """Return True if path looks like a project root."""
    markers = (
        ".git", "pyproject.toml", "setup.py", "setup.cfg",
        "package.json", "Cargo.toml", "go.mod", "requirements.txt",
    )
    return any((path / m).exists() for m in markers)


def get_repo_map(cwd: str) -> str:
    """
    Return a compact code-structure summary string, or '' if:
    - repo_map setting is disabled
    - cwd is not a project root
    - no Python files with symbols found
    """
    from local_cli_agent import settings as _settings
    if not _settings.get("repo_map"):
        return ""

    cwd_path = Path(cwd)
    if not _is_project_root(cwd_path):
        return ""

    # Collect .py files respecting skip-dirs and file limit
    py_files: list[str] = []
    for root, dirs, files in os.walk(cwd):
        dirs[:] = sorted(d for d in dirs if d not in _SKIP_DIRS)
        for fname in sorted(files):
            if fname.endswith(".py"):
                py_files.append(os.path.join(root, fname))
        if len(py_files) >= _MAX_FILES:
            break

    if not py_files:
        return ""

    output: list[str] = ["--- REPO-MAP (Codestruktur) ---"]
    total_lines = 0

    for fpath in py_files[:_MAX_FILES]:
        symbols = _parse_python(fpath)
        if not symbols:
            continue
        try:
            rel = os.path.relpath(fpath, cwd)
        except ValueError:
            rel = fpath
        output.append(rel)
        output.extend(symbols)
        total_lines += 1 + len(symbols)
        if total_lines >= _MAX_LINES:
            output.append("  ... (weitere Dateien gekürzt)")
            break

    if len(output) <= 1:
        return ""

    output.append("--- ENDE REPO-MAP ---")
    return "\n".join(output)
