# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Steffen Schwabe
"""
project.py — Automatic project context detection.

On every system prompt build, the current working directory is scanned for
project indicators (pyproject.toml, package.json, Cargo.toml, …). The result
is injected into the system prompt so the agent always knows what project it
is working in — without being told explicitly.

Results are cached per (cwd, mtime-fingerprint) so repeated calls are cheap.
"""
import json
import os
import re
import subprocess

# ── Cache ─────────────────────────────────────────────────────────────────────
_cache_key: str = ""
_cache_result: str = ""

# ── Project-type indicators ───────────────────────────────────────────────────
_INDICATORS: dict[str, list[str]] = {
    "Python":     ["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt"],
    "Node.js":    ["package.json"],
    "Rust":       ["Cargo.toml"],
    "Go":         ["go.mod"],
    "Java":       ["pom.xml", "build.gradle", "build.gradle.kts"],
    "PHP":        ["composer.json"],
    "Ruby":       ["Gemfile"],
    ".NET":       ["*.csproj", "*.sln"],
    "Flutter":    ["pubspec.yaml"],
}

# ── Test framework hints ──────────────────────────────────────────────────────
_TEST_HINTS: list[tuple[str, str]] = [
    ("pytest.ini", "pytest"), ("conftest.py", "pytest"),
    ("jest.config.*", "Jest"), ("vitest.config.*", "Vitest"),
    ("*.test.ts", "Jest/Vitest"), ("*.spec.ts", "Jest/Vitest"),
    ("Makefile", "make test"),
]


def _fingerprint(cwd: str) -> str:
    """Cheap fingerprint: mtime of key files in cwd."""
    key_files = [
        "pyproject.toml", "package.json", "Cargo.toml", "go.mod",
        "README.md", ".git/HEAD",
    ]
    parts = [cwd]
    for f in key_files:
        p = os.path.join(cwd, f)
        try:
            parts.append(str(int(os.path.getmtime(p))))
        except OSError:
            parts.append("0")
    return "|".join(parts)


def _detect_languages(cwd: str) -> list[str]:
    langs = []
    for lang, indicators in _INDICATORS.items():
        for ind in indicators:
            if "*" in ind:
                import glob
                if glob.glob(os.path.join(cwd, ind)):
                    langs.append(lang)
                    break
            elif os.path.exists(os.path.join(cwd, ind)):
                langs.append(lang)
                break
    return langs


def _read_python_meta(cwd: str) -> dict:
    info = {}
    path = os.path.join(cwd, "pyproject.toml")
    if os.path.exists(path):
        try:
            text = open(path, encoding="utf-8").read()
            for key, pat in [("name", r'name\s*=\s*["\']([^"\']+)'),
                              ("version", r'version\s*=\s*["\']([^"\']+)'),
                              ("description", r'description\s*=\s*["\']([^"\']+)')]:
                m = re.search(pat, text)
                if m:
                    info[key] = m.group(1)
        except Exception:
            pass
    req = os.path.join(cwd, "requirements.txt")
    if os.path.exists(req):
        try:
            lines = open(req, encoding="utf-8").read().splitlines()
            deps = [l.split("==")[0].split(">=")[0].strip() for l in lines
                    if l.strip() and not l.startswith("#")][:8]
            if deps:
                info["deps"] = ", ".join(deps)
        except Exception:
            pass
    return info


def _read_node_meta(cwd: str) -> dict:
    info = {}
    path = os.path.join(cwd, "package.json")
    if os.path.exists(path):
        try:
            data = json.loads(open(path, encoding="utf-8").read())
            for key in ("name", "version", "description"):
                if data.get(key):
                    info[key] = str(data[key])
            deps = list(data.get("dependencies", {}).keys())[:6]
            dev_deps = list(data.get("devDependencies", {}).keys())[:4]
            if deps:
                info["deps"] = ", ".join(deps)
            if dev_deps:
                info["dev_deps"] = ", ".join(dev_deps)
        except Exception:
            pass
    return info


def _read_git_info(cwd: str) -> dict:
    info = {}
    try:
        branch = subprocess.run(
            "git branch --show-current", shell=True, capture_output=True,
            text=True, cwd=cwd, timeout=3,
        ).stdout.strip()
        if branch:
            info["branch"] = branch
        last = subprocess.run(
            "git log --oneline -1", shell=True, capture_output=True,
            text=True, cwd=cwd, timeout=3,
        ).stdout.strip()
        if last:
            info["last_commit"] = last
    except Exception:
        pass
    return info


def _read_readme_summary(cwd: str) -> str:
    for name in ("README.md", "readme.md", "README.txt", "README"):
        p = os.path.join(cwd, name)
        if os.path.exists(p):
            try:
                lines = open(p, encoding="utf-8", errors="replace").read().splitlines()
                for line in lines[:30]:
                    clean = line.strip().lstrip("#").strip()
                    if len(clean) > 15 and not clean.startswith("!["): # skip image lines
                        return clean[:180]
            except Exception:
                pass
    return ""


def _detect_test_framework(cwd: str) -> str:
    import glob as _glob
    for pattern, label in _TEST_HINTS:
        if "*" in pattern:
            if _glob.glob(os.path.join(cwd, "**", pattern), recursive=True):
                return label
        elif os.path.exists(os.path.join(cwd, pattern)):
            return label
    return ""


def get_project_context(cwd: str) -> str:
    """
    Return a short project context string for the system prompt.
    Returns "" if no recognisable project is found.
    Cached per cwd+mtime fingerprint.
    """
    global _cache_key, _cache_result

    fp = _fingerprint(cwd)
    if fp == _cache_key:
        return _cache_result

    langs = _detect_languages(cwd)
    has_git = os.path.exists(os.path.join(cwd, ".git"))

    if not langs and not has_git:
        _cache_key, _cache_result = fp, ""
        return ""

    meta: dict = {}
    if "Python" in langs:
        meta.update(_read_python_meta(cwd))
    if "Node.js" in langs:
        meta.update(_read_node_meta(cwd))

    git = _read_git_info(cwd) if has_git else {}
    readme = _read_readme_summary(cwd)
    test_fw = _detect_test_framework(cwd)

    lines = ["--- PROJEKT-KONTEXT ---"]

    name_ver = meta.get("name", "")
    if meta.get("version"):
        name_ver += f" v{meta['version']}"
    if name_ver:
        lines.append(f"Projekt: {name_ver}")
    if meta.get("description"):
        lines.append(f"Beschreibung: {meta['description']}")
    elif readme:
        lines.append(f"Zweck: {readme}")

    if langs:
        lines.append(f"Sprache/Stack: {', '.join(langs)}")
    if meta.get("deps"):
        lines.append(f"Abhängigkeiten: {meta['deps']}")
    if test_fw:
        lines.append(f"Test-Framework: {test_fw}")
    if git.get("branch"):
        line = f"Git-Branch: {git['branch']}"
        if git.get("last_commit"):
            line += f"  |  Letzter Commit: {git['last_commit']}"
        lines.append(line)

    lines.append("--- ENDE PROJEKT-KONTEXT ---")
    result = "\n".join(lines)

    _cache_key, _cache_result = fp, result
    return result
