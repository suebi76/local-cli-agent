# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Steffen Schwabe
"""
backends.py – Ollama & LM Studio HTTP backend.

Discovers running services, lists available models, and streams
chat completions via the OpenAI-compatible /v1/chat/completions endpoint.
"""
import itertools
import json
import os
import threading
import time
from dataclasses import dataclass

import requests

from local_cli_agent.constants import RESET, BOLD, DIM, CYAN, GREEN, YELLOW, RED
from local_cli_agent.tools import TOOLS


# ── Spinner ───────────────────────────────────────────────────────────────────
def _run_spinner(stop_event: threading.Event, label: str = "Generiere") -> None:
    """Background spinner shown while waiting for the first response token."""
    frames = itertools.cycle("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏")
    while not stop_event.is_set():
        print(f"\r  {DIM}{next(frames)} {label}...{RESET}", end="", flush=True)
        time.sleep(0.1)
    print(f"\r{' ' * 40}\r", end="", flush=True)  # clear spinner line


def _start_spinner(label: str = "Generiere"):
    """Start spinner in background thread. Returns (stop_event, thread)."""
    stop = threading.Event()
    t = threading.Thread(target=_run_spinner, args=(stop, label), daemon=True)
    t.start()
    return stop, t


def _stop_spinner(stop_event: threading.Event, thread: threading.Thread) -> None:
    stop_event.set()
    thread.join()


# ── Service URLs (overridable via .env) ───────────────────────────────────────
_OLLAMA_URL   = os.environ.get("LOCAL_CLI_OLLAMA_URL",   "http://localhost:11434")
_LMSTUDIO_URL = os.environ.get("LOCAL_CLI_LMSTUDIO_URL", "http://localhost:1234")

_DETECT_TIMEOUT  = 1.5  # seconds – service reachability probe
_CONNECT_TIMEOUT = 10   # seconds – initial connection to backend
_STREAM_TIMEOUT  = 300  # seconds – max wait between two SSE chunks (5 min)


# ── ModelEntry ────────────────────────────────────────────────────────────────
@dataclass
class ModelEntry:
    name: str              # Display name, e.g. "llama3.2:3b"
    model_id: str          # API identifier, e.g. "llama3.2:3b"
    backend: str           # "ollama" | "lmstudio"
    base_url: str          # "http://localhost:11434"
    size_gb: float         # 0.0 if unknown
    description: str       # "3.2B · general purpose"
    supports_tools: bool = True   # False → skip function-calling payload


# ── Service detection ─────────────────────────────────────────────────────────
def detect_services() -> dict:
    """Check which services are reachable. Returns {"ollama": bool, "lmstudio": bool}."""
    result = {"ollama": False, "lmstudio": False}
    try:
        r = requests.get(f"{_OLLAMA_URL}/api/tags", timeout=_DETECT_TIMEOUT)
        result["ollama"] = r.status_code == 200
    except Exception:
        pass
    try:
        r = requests.get(f"{_LMSTUDIO_URL}/v1/models", timeout=_DETECT_TIMEOUT)
        result["lmstudio"] = r.status_code == 200
    except Exception:
        pass
    return result


# ── Architecture hints ────────────────────────────────────────────────────────
_ARCH_HINTS = {
    "qwen":       "code / reasoning",
    "gemma":      "chat / vision",
    "llama":      "general purpose",
    "mistral":    "general purpose",
    "phi":        "small / fast",
    "deepseek":   "code / reasoning",
    "falcon":     "general purpose",
    "vicuna":     "chat",
    "codellama":  "code generation",
    "starcoder":  "code generation",
}


def _arch_hint(name: str) -> str:
    name_lower = name.lower()
    return next((hint for kw, hint in _ARCH_HINTS.items() if kw in name_lower), "general purpose")


# ── Ollama ────────────────────────────────────────────────────────────────────
def list_ollama_models(base_url: str = "") -> list:
    """GET /api/tags → list of ModelEntry. Uses _OLLAMA_URL if base_url is empty."""
    url = base_url or _OLLAMA_URL
    try:
        r = requests.get(f"{url}/api/tags", timeout=_DETECT_TIMEOUT)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return []

    entries = []
    for m in data.get("models", []):
        name = m.get("name", "")
        if not name:
            continue
        size_bytes = m.get("size", 0)
        size_gb = size_bytes / (1024 ** 3) if size_bytes else 0.0
        # Optional parameter size from details (e.g. "3.2B")
        details = m.get("details", {})
        param_size = details.get("parameter_size", "")
        desc_prefix = f"{param_size} · " if param_size else ""
        entries.append(ModelEntry(
            name=name,
            model_id=name,
            backend="ollama",
            base_url=url,
            size_gb=size_gb,
            description=f"{desc_prefix}{_arch_hint(name)}",
        ))
    return entries


# ── LM Studio ────────────────────────────────────────────────────────────────
def list_lmstudio_models(base_url: str = "") -> list:
    """
    Query LM Studio for available models.
    Prefers the extended /api/v0/models endpoint (only loaded models, richer info).
    Falls back to /v1/models if the extended endpoint is unavailable.
    """
    url = base_url or _LMSTUDIO_URL

    # ── Try extended endpoint first ───────────────────────────────────────────
    try:
        r = requests.get(f"{url}/api/v0/models", timeout=_DETECT_TIMEOUT)
        if r.status_code == 200:
            data = r.json()
            entries = []
            for m in data.get("data", []):
                model_id = m.get("id", "")
                if not model_id:
                    continue
                # Only include currently loaded models
                if m.get("state", "not-loaded") != "loaded":
                    continue
                ctx = m.get("loaded_context_length") or m.get("max_context_length", 0)
                ctx_str = f" · ctx {ctx // 1024}k" if ctx else ""
                caps = m.get("capabilities", [])
                supports_tools = "tool_use" in caps
                entries.append(ModelEntry(
                    name=model_id,
                    model_id=model_id,
                    backend="lmstudio",
                    base_url=url,
                    size_gb=0.0,
                    description=f"{_arch_hint(model_id)}{ctx_str}",
                    supports_tools=supports_tools,
                ))
            return entries
    except Exception:
        pass

    # ── Fallback: standard OpenAI endpoint (all models, no state info) ────────
    try:
        r = requests.get(f"{url}/v1/models", timeout=_DETECT_TIMEOUT)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return []

    entries = []
    for m in data.get("data", []):
        model_id = m.get("id", "")
        if not model_id:
            continue
        entries.append(ModelEntry(
            name=model_id,
            model_id=model_id,
            backend="lmstudio",
            base_url=url,
            size_gb=0.0,
            description=_arch_hint(model_id),
        ))
    return entries


# ── Combined list ─────────────────────────────────────────────────────────────
def list_all_models() -> list:
    """Return all models: Ollama first, then LM Studio."""
    models = []
    models.extend(list_ollama_models())
    models.extend(list_lmstudio_models())
    return models


# ── Model compatibility ───────────────────────────────────────────────────────

# Patterns that indicate a model is unsuitable for agent/tool-use tasks
_UNSUITABLE_PATTERNS = [
    ("embed",     "Embedding-Modell – kann keinen Text generieren"),
    ("rerank",    "Reranking-Modell – nicht für Gespräche geeignet"),
    ("whisper",   "Audio-Modell – nicht für Text-Chat geeignet"),
    ("reasoning", "Reasoning-/Denkmodell – schlechte Tool-Use-Performance"),
    ("thinking",  "Thinking-Modell – schlechte Tool-Use-Performance"),
    ("reflect",   "Reflection-Modell – schlechte Tool-Use-Performance"),
]

# Curated list of models known to work well as coding agents
RECOMMENDED_MODELS = [
    ("qwen2.5-coder:7b",  "4.7 GB", "Code + Tool-Use, ideal für diesen Agent"),
    ("qwen2.5-coder:14b", "9.0 GB", "Code + Tool-Use, größer & besser"),
    ("llama3.2:3b",       "2.0 GB", "Sehr schnell, allgemein, gute Tool-Use"),
    ("llama3.1:8b",       "4.7 GB", "Allgemein, zuverlässig"),
    ("mistral:7b",        "4.1 GB", "Zuverlässig, allgemein"),
    ("phi4-mini",         "2.5 GB", "Klein, schnell, überraschend gut"),
    ("gemma3:4b",         "3.3 GB", "Allgemein, flott"),
]


def check_model_compatibility(entry: ModelEntry) -> dict:
    """
    Check if a model is suitable for agent/tool-use tasks.
    Returns {"ok": True} or {"ok": False, "reason": str}.
    """
    name_lower = entry.name.lower()
    for pattern, reason in _UNSUITABLE_PATTERNS:
        if pattern in name_lower:
            return {"ok": False, "reason": reason}
    return {"ok": True}


# ── No-service help text ──────────────────────────────────────────────────────
def print_no_service_help() -> None:
    print(f"\n{YELLOW}Kein Modell-Backend gefunden.{RESET}\n")
    print(f"Bitte installiere {BOLD}Ollama{RESET} oder {BOLD}LM Studio{RESET}:\n")
    print(f"  {CYAN}OLLAMA{RESET} (empfohlen – kostenlos, einfach):")
    print(f"    1. https://ollama.com herunterladen und installieren")
    print(f"    2. Modell laden:  {DIM}ollama pull llama3.2{RESET}")
    print(f"    3. local-cli starten\n")
    print(f"  {CYAN}LM STUDIO{RESET} (mit GUI, Modell-Browser):")
    print(f"    1. https://lmstudio.ai herunterladen")
    print(f"    2. Modell herunterladen (in LM Studio)")
    print(f"    3. Tab \"Local Server\" → \"Start Server\"")
    print(f"    4. local-cli starten\n")
    print(f"{DIM}Tipp: Beide Dienste können gleichzeitig laufen.{RESET}\n")


# ── Streaming API call ────────────────────────────────────────────────────────
def call_api(entry: ModelEntry, messages: list, max_tokens: int = 4096, use_tools: bool = True):
    """
    POST /v1/chat/completions with SSE streaming.
    Automatically retries once on ConnectionError.
    Returns (full_content, tool_calls) or (None, None) on unrecoverable error.
    """
    for attempt in range(2):
        result = _stream_once(entry, messages, max_tokens, use_tools)
        if result is not None:
            return result
        # result is None → ConnectionError on this attempt
        if attempt == 0:
            print(f"\n{YELLOW}Verbindung unterbrochen – versuche neu...{RESET}", flush=True)
        else:
            # Second failure → give up with helpful hint
            backend_hint = ""
            if entry.backend == "lmstudio":
                backend_hint = (
                    f"\n{DIM}Tipp: In LM Studio → Context Length reduzieren "
                    f"oder Modell neu laden.{RESET}"
                )
            print(f"\n{RED}Verbindung zum Backend verloren ({entry.backend}).{RESET}{backend_hint}")
    return None, None


def _stream_once(entry: ModelEntry, messages: list, max_tokens: int, use_tools: bool):
    """
    Single streaming attempt. Returns (content, tool_calls) on success,
    or None on ConnectionError (caller should retry), or (None, None) on other errors.
    """
    url = f"{entry.base_url}/v1/chat/completions"

    payload = {
        "model": entry.model_id,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "stream": True,
    }
    if use_tools and TOOLS and getattr(entry, "supports_tools", True):
        payload["tools"] = TOOLS
        payload["tool_choice"] = "auto"

    full_content = ""
    content_started = False
    tool_calls_acc: dict = {}
    spinner_stopped = False

    # ── Rich output mode (buffer chunks, render complete response) ────────────
    from local_cli_agent import settings as _settings
    from local_cli_agent import rendering as _rendering
    _use_rich = _rendering.is_available() and bool(_settings.get("rich_output"))

    # ── Thinking-block state (for models like gemma-reasoning, qwen3) ─────────
    in_thinking = False
    thinking_shown = False   # True once "Denke..." was printed

    # ── Spinner: shown while waiting for first token ──────────────────────────
    spin_stop, spin_thread = _start_spinner("Generiere")

    def _ensure_spinner_stopped():
        nonlocal spinner_stopped
        if not spinner_stopped:
            _stop_spinner(spin_stop, spin_thread)
            spinner_stopped = True

    try:
        resp = requests.post(
            url, json=payload, stream=True,
            timeout=(_CONNECT_TIMEOUT, _STREAM_TIMEOUT),
        )
        resp.raise_for_status()

        for raw_line in resp.iter_lines():
            if not raw_line:
                continue
            line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
            if not line.startswith("data: "):
                continue
            data_str = line[6:]
            if data_str.strip() == "[DONE]":
                break

            try:
                chunk = json.loads(data_str)
            except json.JSONDecodeError:
                continue

            choices = chunk.get("choices", [])
            if not choices:
                continue
            delta = choices[0].get("delta", {})
            finish = choices[0].get("finish_reason")

            # ── Tool calls ────────────────────────────────────────────────
            for tc in delta.get("tool_calls") or []:
                _ensure_spinner_stopped()
                idx = tc.get("index", 0)
                if idx not in tool_calls_acc:
                    tool_calls_acc[idx] = {
                        "id": tc.get("id", f"call_{idx}"),
                        "name": "",
                        "arguments": "",
                    }
                if tc.get("id"):
                    tool_calls_acc[idx]["id"] = tc["id"]
                fn = tc.get("function") or {}
                if fn.get("name"):
                    tool_calls_acc[idx]["name"] = fn["name"]
                if fn.get("arguments"):
                    tool_calls_acc[idx]["arguments"] += fn["arguments"]

            # ── Content (with thinking-block filter) ──────────────────────
            content_chunk = delta.get("content") or ""
            if not content_chunk:
                if finish in ("stop", "tool_calls"):
                    break
                continue

            # Detect start/end of thinking blocks (<|think|> ... <|/think|>)
            if "<|think|>" in content_chunk:
                before = content_chunk[:content_chunk.find("<|think|>")]
                in_thinking = True
                if before:
                    if not content_started:
                        content_started = True
                        if not _use_rich:
                            print(f"\n{BOLD}{GREEN}Agent:{RESET} ", end="", flush=True)
                    full_content += before
                    if not _use_rich:
                        print(before, end="", flush=True)
                if not thinking_shown:
                    _ensure_spinner_stopped()
                    print(f"\n{DIM}Denke...{RESET}", end="", flush=True)
                    thinking_shown = True
                if finish in ("stop", "tool_calls"):
                    break
                continue

            if "<|/think|>" in content_chunk:
                after = content_chunk[content_chunk.find("<|/think|>") + len("<|/think|>"):]
                in_thinking = False
                if thinking_shown:
                    # Clear the "Denke..." line
                    print(f"\r{' ' * 20}\r", end="", flush=True)
                    thinking_shown = False
                content_chunk = after

            if in_thinking:
                # Suppress thinking content from display
                if finish in ("stop", "tool_calls"):
                    break
                continue

            if content_chunk:
                if not content_started:
                    _ensure_spinner_stopped()
                    content_started = True
                    if not _use_rich:
                        print(f"\n{BOLD}{GREEN}Agent:{RESET} ", end="", flush=True)
                full_content += content_chunk
                if not _use_rich:
                    print(content_chunk, end="", flush=True)

            if finish in ("stop", "tool_calls"):
                break

    except KeyboardInterrupt:
        _ensure_spinner_stopped()
        print(f"\n{DIM}Antwort abgebrochen.{RESET}")
        if content_started:
            print(RESET)
        return full_content, None

    except requests.exceptions.Timeout:
        _ensure_spinner_stopped()
        print(f"\n{RED}Timeout – keine Antwort vom Modell (>{_STREAM_TIMEOUT}s).{RESET}")
        return None, None

    except requests.exceptions.ConnectionError:
        _ensure_spinner_stopped()
        # Signal to caller that a retry may help
        return None  # type: ignore[return-value]

    except Exception as exc:
        _ensure_spinner_stopped()
        print(f"\n{RED}API-Fehler: {exc}{RESET}")
        return None, None

    _ensure_spinner_stopped()
    if _use_rich and full_content:
        print(f"\n{BOLD}{GREEN}Agent:{RESET}")
        _rendering.render(full_content)
    elif content_started:
        print(RESET)

    # Build structured tool_calls list
    tool_calls = None
    if tool_calls_acc:
        tool_calls = [
            {
                "id": tc["id"],
                "type": "function",
                "function": {"name": tc["name"], "arguments": tc["arguments"]},
            }
            for tc in (tool_calls_acc[i] for i in sorted(tool_calls_acc))
        ]

    return full_content, tool_calls