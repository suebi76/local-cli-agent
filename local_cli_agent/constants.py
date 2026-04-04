import os

# ── ANSI Colors ──────────────────────────────────────────────────────────────
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
RED = "\033[31m"
BLUE = "\033[34m"
WHITE = "\033[37m"

# ── Config ───────────────────────────────────────────────────────────────────
API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL = "moonshotai/kimi-k2.5"
# local_cli_agent/ is one level below the project root
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# self_improve targets cli.py as the package entry point
SCRIPT_FILE = os.path.join(SCRIPT_DIR, "local_cli_agent", "cli.py")
ENV_FILE = os.path.join(SCRIPT_DIR, ".env")
MEMORY_FILE = os.path.join(SCRIPT_DIR, ".local-cli-memory.json")
CHANGELOG = os.path.join(SCRIPT_DIR, ".local-cli-changelog.json")
VERSION = "1.2.0"
