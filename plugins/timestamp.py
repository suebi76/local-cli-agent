"""
Kimi K2.5 Plugin: timestamp
Returns current date and time.
"""
from datetime import datetime

TOOL_DEF = {
    "type": "function",
    "function": {
        "name": "timestamp",
        "description": "Returns current date and time. Useful when the user asks what time or date it is.",
        "parameters": {
            "type": "object",
            "properties": {
                "format": {
                    "type": "string",
                    "description": "Date format string (default: '%Y-%m-%d %H:%M:%S'). Examples: '%d.%m.%Y %H:%M', '%H:%M:%S'"
                }
            },
            "required": []
        }
    }
}


def execute(args):
    """Execute the tool. Returns formatted timestamp."""
    fmt = args.get("format", "%Y-%m-%d %H:%M:%S")
    return datetime.now().strftime(fmt)
