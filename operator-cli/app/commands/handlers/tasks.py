def result(parts, api):
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