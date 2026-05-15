"""Handlers for show commands in the operator CLI.

This module implements `show agents`, `show tasks`, and `show agent <id>`.
"""

def show_agents(parts, api):
    """Handle the `show agents` command."""
    status = None
    if len(parts) > 2 and parts[2].lower() == "online":
        status = "online"
    return api.agents.list(status=status)

def show_tasks(parts, api):
    status = None
    agent_id = None
    for i, p in enumerate(parts[2:]):
        if p.lower() == "status" and i + 2 < len(parts):
            status = parts[2 + i + 1]
        if p.lower() == "on" and i + 2 < len(parts):
            agent_id = parts[2 + i + 1]
    return api.tasks.list(agent_id=agent_id, status=status)

def show_agent(agent_id, api):
    return api.agents.get(agent_id)

def show(parts, api):
    if len(parts) < 2:
        return {"error": "Usage: show agents | show tasks | show agent <id>"}
    
    subcmd = parts[1].lower()
    
    if subcmd == "agents":
        return show_agents(parts, api)
    
    if subcmd == "tasks":
        return show_tasks(parts, api)
    
    if subcmd.startswith("agent_"):
        return show_agent(subcmd, api)
    
    return {"error": f"Unknown show command: {subcmd}"}