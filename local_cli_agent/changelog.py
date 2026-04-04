import os
import json
from datetime import datetime

from local_cli_agent.constants import CHANGELOG, VERSION, SCRIPT_DIR

_LEGACY_CHANGELOG = os.path.join(SCRIPT_DIR, ".kimi-changelog.json")


def _migrate_changelog():
    """Migrate legacy .kimi-changelog.json to new name if needed."""
    if not os.path.exists(CHANGELOG) and os.path.exists(_LEGACY_CHANGELOG):
        try:
            os.rename(_LEGACY_CHANGELOG, CHANGELOG)
        except OSError:
            pass


# ── Changelog ───────────────────────────────────────────────────────────────
def add_changelog_entry(description):
    """Add an entry to the changelog."""
    _migrate_changelog()
    log = []
    if os.path.exists(CHANGELOG):
        try:
            with open(CHANGELOG, "r", encoding="utf-8") as f:
                log = json.load(f)
        except (json.JSONDecodeError, IOError):
            log = []
    log.append({
        "date": datetime.now().isoformat(),
        "version": VERSION,
        "description": description,
    })
    with open(CHANGELOG, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)


def get_changelog():
    """Get the changelog as a string."""
    _migrate_changelog()
    if not os.path.exists(CHANGELOG):
        return "No changelog entries yet."
    try:
        with open(CHANGELOG, "r", encoding="utf-8") as f:
            log = json.load(f)
        lines = []
        for entry in log[-20:]:  # Last 20 entries
            lines.append(f" [{entry['date'][:16]}] v{entry['version']}: {entry['description']}")
        return "\n".join(lines) if lines else "No entries."
    except Exception:
        return "Error reading changelog."
