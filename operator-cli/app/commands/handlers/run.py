def run(parts, api):
    try:
        on_idx = parts.index("on")
        if on_idx < 2 or on_idx >= len(parts) - 1:
            return {"error": "Usage: run <command> on <agent_id>"}
        
        command = parts[1]
        agent_id = parts[on_idx + 1]
        
        if command == "whoami":
            payload = {}
        elif command == "uptime":
            payload = {}
        elif command == "shell_execute":
            payload = {"command": "echo 'shell_execute needs command argument'"}
        else:
            return {"error": f"Unknown command: {command}. Allowed: whoami, uptime, shell_execute"}
        
        return api.tasks.create(agent_id, command, payload)
    except ValueError:
        return {"error": "Usage: run <command> on <agent_id>"}
    except Exception as e:
        err_str = str(e)
        if "404" in err_str:
            return {"error": f"Unknown agent: {parts[parts.index('on') + 1]}"}
        return {"error": err_str}