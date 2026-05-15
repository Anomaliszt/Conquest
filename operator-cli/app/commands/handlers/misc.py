"""Miscellaneous CLI command handlers.

Includes help text and terminal control actions.
"""

def help():
    """Return help metadata for available CLI commands."""
    return {
        "help": [
            "login [username] [password] - Authenticate",
            "show agents [online] - List all agents",
            "show agent <id> - Get agent details",
            "show tasks [status] - List tasks",
            "run <command> on <agent> - Execute command",
            "cancel <task_id> - Cancel a task",
            "status - Show connection status",
            "logout - Clear credentials",
            "clear - Clear screen",
            "help - Show this help"
        ]
    }

def clear():
    return {"action": "clear"}