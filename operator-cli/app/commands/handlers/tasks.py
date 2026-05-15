"""Task command handlers for the CLI.

Supports fetching task results and cancelling tasks.
"""

def result(parts, api):
    """Handle the `result` command for a task."""
    if len(parts) < 2:
        return {"error": "Usage: result <task_id>"}
    task_id = parts[1]
    try:
        return api.tasks.result(task_id)
    except Exception as e:
        return {"error": str(e)}

def cancel(parts, api):
    if len(parts) < 2:
        return {"error": "Usage: cancel <task_id>"}
    task_id = parts[1]
    try:
        return api.tasks.cancel(task_id)
    except Exception as e:
        return {"error": str(e)}