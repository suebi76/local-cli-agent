import os
import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.history import InMemoryHistory

from local_cli_agent.constants import (
    RESET, BOLD, DIM, CYAN, GREEN, YELLOW, MAGENTA, RED, BLUE,
    VERSION, SCRIPT_FILE,
)
from local_cli_agent.config import build_system_prompt, load_api_key, save_api_key
from local_cli_agent.memory import load_memory
from local_cli_agent.changelog import get_changelog
from local_cli_agent.agent import agent_loop
from local_cli_agent.api import call_api
import local_cli_agent.executor as executor

_SLASH_COMMANDS = [
    "/thinking", "/auto", "/clear", "/cd", "/memory",
    "/history", "/tokens", "/reload", "/version", "/changelog",
    "/help", "/quit",
]


class _SlashCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if not text.startswith("/"):
            return
        word = text.split()[0] if text.split() else text
        for cmd in _SLASH_COMMANDS:
            if cmd.startswith(word):
                yield Completion(cmd, start_position=-len(word), display_meta=_CMD_META.get(cmd, ""))


_CMD_META = {
    "/thinking": "Toggle reasoning mode on/off",
    "/auto":     "Toggle auto-approve tool calls",
    "/clear":    "Clear conversation history",
    "/cd":       "Change working directory",
    "/memory":   "List saved memories",
    "/history":  "Show message history",
    "/tokens":   "Set max output tokens",
    "/reload":   "Reload after self-improvement",
    "/version":  "Show version info",
    "/changelog":"Show self-improvement history",
    "/help":     "Show help",
    "/quit":     "Exit",
}


def print_banner():
    """Print the startup banner."""
    print(f"""
{BOLD}{CYAN}╔══════════════════════════════════════════════════════════════════╗
║{YELLOW}                 Local CLI Agent v{VERSION}                  {CYAN}║
║{MAGENTA}                 Moonshot AI via NVIDIA NIM API                  {CYAN}║
║{GREEN}              Self-improving AI coding assistant                  {CYAN}║
╚══════════════════════════════════════════════════════════════════╝{RESET}
{DIM}Tools: bash • files • edit • grep • glob • web • memory • self-improve{RESET}

{DIM}Commands:{RESET}
  {YELLOW}/thinking on|off{RESET}  Toggle thinking/reasoning mode
  {YELLOW}/auto on|off{RESET}      Auto-approve tool execution
  {YELLOW}/clear{RESET}            Clear conversation history
  {YELLOW}/cd <path>{RESET}        Change working directory
  {YELLOW}/memory{RESET}           List saved memories
  {YELLOW}/reload{RESET}           Reload after self-improvement
  {YELLOW}/version{RESET}          Show version info
  {YELLOW}/changelog{RESET}        Show self-improvement history
  {YELLOW}/help{RESET}             Show this help
  {YELLOW}/quit{RESET}             Exit (or Ctrl+C)

{DIM}Press 'a' at any tool prompt to auto-approve all.{RESET}
""")


def interactive_mode(thinking=True, system_prompt=None, max_tokens=16384):
    """Run interactive chat loop."""
    print_banner()

    messages = [{"role": "system", "content": build_system_prompt(system_prompt)}]

    mode_str = f"{MAGENTA}thinking{RESET}" if thinking else f"{BLUE}instant{RESET}"
    auto_str = f"{GREEN}on{RESET}" if executor.auto_approve else f"{RED}off{RESET}"
    print(f"{DIM}Mode: {mode_str} {DIM}| Auto-approve: {auto_str} {DIM}| Tokens: {max_tokens}{RESET}")
    print(f"{DIM}CWD: {os.getcwd()}{RESET}\n")

    session = PromptSession(
        completer=_SlashCompleter(),
        history=InMemoryHistory(),
        complete_while_typing=True,
    )

    while True:
        try:
            lines = []
            while True:
                prompt_str = ANSI(f"\n{BOLD}{CYAN}You:{RESET} ") if not lines else ANSI(f" {DIM}...{RESET} ")
                line = session.prompt(prompt_str)
                if line == "" and lines:
                    break
                if line == "" and not lines:
                    continue
                lines.append(line)
                if len(lines) == 1 and not line.endswith("\\"):
                    break
                if line.endswith("\\"):
                    lines[-1] = line[:-1]
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
                    executor.auto_approve = cmd[1].lower() == "on"
                else:
                    executor.auto_approve = not executor.auto_approve
                auto_str = f"{GREEN}on{RESET}" if executor.auto_approve else f"{RED}off{RESET}"
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
                        print(f" {CYAN}{k}{RESET}: {DIM}{preview}{RESET}")
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
                        print(f" {CYAN}[you] {content[:80]}{RESET}")
                        count += 1
                    elif role == "assistant":
                        tc = msg.get("tool_calls")
                        if tc:
                            names = ", ".join(t["function"]["name"] for t in tc)
                            print(f" {GREEN}[agent] {content[:60]} [tools: {names}]{RESET}")
                        else:
                            print(f" {GREEN}[agent] {content[:80]}{RESET}")
                        count += 1
                    elif role == "tool":
                        print(f" {DIM}[tool] {content[:60]}...{RESET}")
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
                print(f"{YELLOW}Reloading Local CLI Agent...{RESET}")
                os.execv(sys.executable, [sys.executable, "-m", "local_cli_agent.cli"] + sys.argv[1:])
            elif cmd_lower == "/version":
                print(f"{DIM}Local CLI Agent v{VERSION}{RESET}")
                print(f"{DIM}Source: {SCRIPT_FILE}{RESET}")
                print()
                continue
            elif cmd_lower == "/changelog":
                cl = get_changelog()
                print(f"{DIM}{cl}{RESET}\n")
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
    print(f"\n{BOLD}{CYAN}Local CLI Agent Setup{RESET}")
    print(f"{DIM}Get your free API key at: https://build.nvidia.com/moonshotai/kimi-k2.5{RESET}\n")
    key = input(f"{BOLD}Enter your NVIDIA API Key: {RESET}").strip()
    if not key:
        print(f"{RED}No key entered.{RESET}")
        return
    save_api_key(key)
    print(f"\n{DIM}Testing connection...{RESET}")
    messages = [{"role": "user", "content": "Say 'Hello! Local CLI Agent is ready.' in exactly those words."}]
    content, _ = call_api(messages, thinking=False, max_tokens=64, use_tools=False)
    if content:
        print(f"\n{GREEN}Setup complete! Run 'local-cli' to start.{RESET}\n")
    else:
        print(f"\n{YELLOW}Key saved but test failed. Check your API key.{RESET}\n")
