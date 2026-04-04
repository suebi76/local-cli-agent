import sys
import os
import signal
import argparse

# Fix Windows console encoding for Unicode output — must run before any print
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    os.system("")  # Enable ANSI escape codes on Windows

from local_cli_agent.constants import RESET, DIM, YELLOW
import local_cli_agent.executor as executor
from local_cli_agent.config import load_api_key
from local_cli_agent.ui import interactive_mode, oneshot_mode, setup_mode


def main():
    parser = argparse.ArgumentParser(
        description="Local CLI Agent - AI coding assistant with full tool use",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  local-cli                           Interactive agent chat
  local-cli --instant                 Fast mode (no reasoning)
  local-cli "Create a React project"  One-shot with tools
  local-cli --setup                   Configure API key
  local-cli -s "You are a Go expert"  Custom system prompt
  local-cli --auto                    Auto-approve all actions
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

    if args.auto:
        executor.auto_approve = True

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
