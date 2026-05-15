from rich.console import Console
from rich.table import Table

console = Console()

def print_result(result, ctx=None):
    if result is None:
        return
    
    if "error" in result:
        console.print(f"[red]Error: {result['error']}[/red]")
        return
    
    if "success" in result:
        console.print(f"[green]{result['success']}[/green]")
        return
    
    if "action" in result:
        if result["action"] == "start_websocket":
            console.print(f"[yellow]WebSocket streaming not yet implemented[/yellow]")
        return
    
    if isinstance(result, list):
        if not result:
            console.print("[yellow]No results found[/yellow]")
            return
        if "hostname" in result[0]:
            print_agents(result)
        elif "type" in result[0]:
            print_tasks(result)
        else:
            for item in result:
                console.print(item)
    elif isinstance(result, dict):
        if "hostname" in result:
            print_agent(result)
        elif "type" in result:
            print_task(result)
        else:
            for k, v in result.items():
                console.print(f"{k}: {v}")

def print_agents(agents):
    table = Table(title="Agents", show_header=True)
    table.add_column("ID", style="cyan")
    table.add_column("Hostname")
    table.add_column("OS")
    table.add_column("Status")
    table.add_column("Last Seen")
    
    for a in agents:
        status_style = "green" if a.get("status") == "online" else "red"
        table.add_row(
            a.get("id", ""),
            a.get("hostname", ""),
            a.get("os", ""),
            f"[{status_style}]{a.get('status', '')}[/]",
            a.get("last_seen", "")
        )
    
    console.print(table)

def print_agent(agent):
    table = Table(title=f"Agent: {agent.get('id')}", show_header=False)
    for k, v in agent.items():
        if k != "id":
            table.add_row(k, str(v))
    console.print(table)

def print_tasks(tasks):
    table = Table(title="Tasks", show_header=True)
    table.add_column("ID", style="cyan")
    table.add_column("Type")
    table.add_column("Agent")
    table.add_column("Status")
    table.add_column("Created")
    
    for t in tasks:
        status_style = {
            "completed": "green",
            "failed": "red",
            "running": "yellow",
            "queued": "blue"
        }.get(t.get("status", ""), "")
        
        table.add_row(
            t.get("id", ""),
            t.get("type", ""),
            t.get("agent_id", ""),
            f"[{status_style}]{t.get('status', '')}[/]",
            t.get("created_at", "")
        )
    
    console.print(table)

def print_task(task):
    table = Table(title=f"Task: {task.get('id')}", show_header=False)
    for k, v in task.items():
        if k != "id":
            table.add_row(k, str(v))
    console.print(table)