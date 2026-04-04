import sys
import json

import requests

from local_cli_agent.constants import (
    RESET, BOLD, DIM, GREEN, MAGENTA, RED, YELLOW,
    API_URL, MODEL,
)
from local_cli_agent.tools import TOOLS
from local_cli_agent.config import load_api_key


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
                print(f"\n{DIM}{MAGENTA} thinking...{RESET}")
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
