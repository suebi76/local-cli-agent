# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Steffen Schwabe
import sys
import os
import signal
import argparse

# Fix Windows console encoding for Unicode output — must run before any print
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    os.system("")  # Enable ANSI escape codes on Windows

from local_cli_agent._env import load_env_early
load_env_early()

from local_cli_agent.constants import RESET, DIM, YELLOW, RED
import local_cli_agent.executor as executor
from local_cli_agent.ui import interactive_mode, oneshot_mode
from local_cli_agent import api, model_selector
from local_cli_agent.config import load_last_model, save_last_model


def main():
    parser = argparse.ArgumentParser(
        description="Local CLI Agent - AI coding assistant with Ollama / LM Studio backends",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  local-cli                              Interactive agent chat
  local-cli --instant                    Fast mode (no reasoning hints)
  local-cli "Create a React project"     One-shot with tools
  local-cli -s "You are a Go expert"     Custom system prompt
  local-cli --auto                       Auto-approve all actions
  local-cli --watch ./src "fix all TODOs"  Watch mode
""",
    )
    parser.add_argument("prompt", nargs="?", help="One-shot prompt (omit for interactive)")
    parser.add_argument("--instant", action="store_true", help="Instant mode (no thinking)")
    parser.add_argument("-s", "--system", type=str, help="System prompt")
    parser.add_argument("-t", "--tokens", type=int, default=None, help="Max output tokens (default: saved setting or 4096)")
    parser.add_argument("--auto", action="store_true", help="Auto-approve all tool calls")
    parser.add_argument("--watch", nargs=2, metavar=("PATH", "INSTRUCTION"),
                        help="Watch PATH and trigger agent with INSTRUCTION on each change")
    parser.add_argument("--mission", type=str, metavar="GOAL",
                        help="Run mission mode: agent plans and executes GOAL step by step")
    parser.add_argument("--orchestrate", type=str, metavar="GOAL",
                        help="Run orchestrator: master assigns specialists per step for complex tasks")
    args = parser.parse_args()

    signal.signal(signal.SIGINT, lambda *_: (print(f"\n{DIM}Goodbye!{RESET}"), sys.exit(0)))

    if args.auto:
        executor.auto_approve = True

    # ── Model selection ──────────────────────────────────────────────────────
    last = load_last_model()
    entry = model_selector.show_selector(last_model=last)
    if entry is None:
        print(f"\n{DIM}Kein Modell ausgewählt. Auf Wiedersehen!{RESET}\n")
        sys.exit(0)

    # Persist selection for next startup (format: "ollama:llama3.2:3b")
    save_last_model(f"{entry.backend}:{entry.model_id}")

    # Register with api dispatcher
    api.set_entry(entry)

    # ── Start agent ──────────────────────────────────────────────────────────
    thinking = not args.instant

    if args.orchestrate:
        from local_cli_agent import orchestrator as _orchestrator
        from local_cli_agent.agent import agent_loop
        from local_cli_agent.config import build_system_prompt
        messages = [{"role": "system", "content": build_system_prompt()}]
        _orchestrator.run_orchestration(
            goal=args.orchestrate,
            messages=messages,
            agent_callback=agent_loop,
            thinking=thinking,
            max_tokens=args.tokens,
        )
    elif args.mission:
        from local_cli_agent import mission as _mission
        from local_cli_agent.agent import agent_loop
        from local_cli_agent.config import build_system_prompt
        messages = [{"role": "system", "content": build_system_prompt()}]
        _mission.run_mission(
            goal=args.mission,
            messages=messages,
            agent_callback=agent_loop,
            thinking=thinking,
            max_tokens=args.tokens,
        )
    elif args.watch:
        from local_cli_agent import watcher as _watcher
        from local_cli_agent.agent import agent_loop
        watch_path, watch_instr = args.watch
        print(_watcher.start(
            path=watch_path,
            instruction=watch_instr,
            agent_callback=agent_loop,
            thinking=thinking,
            max_tokens=args.tokens,
        ))
        print(f"{DIM}Watch-Mode läuft. Ctrl+C zum Beenden.{RESET}")
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(_watcher.stop())
    elif args.prompt:
        oneshot_mode(args.prompt, thinking=thinking, system_prompt=args.system, max_tokens=args.tokens)
    else:
        interactive_mode(thinking=thinking, system_prompt=args.system, max_tokens=args.tokens)


if __name__ == "__main__":
    main()