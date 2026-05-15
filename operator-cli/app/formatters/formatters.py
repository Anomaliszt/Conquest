"""Terminal output formatters using Rich library.

Provides colored, table-based output for:
- Agent lists and details
- Task lists and details
- Error and success messages
"""

from rich.console import Console
from rich.table import Table


console = Console()


def print_result(result, ctx=None):
    """Format and print command results to terminal.
    
    Routes different result types to appropriate formatters:
    - Error dicts -> red error message
    - Success dicts -> green success message  
    - Lists of agents -> agent table
    - Lists of tasks -> task table
    - Empty lists -> "No results found"
    - Single dicts -> key-value pairs
    
    Args:
        result: Command result to format
        ctx: Optional context (unused, for future expansion)
    """
    if result is None:
        return
    
    # Short-circuit known result shapes before rendering table output.
    # Error messages
    if "error" in result:
        console.print(f"[red]Error: {result['error']}[/red]")
        return
    
    # Success messages
    if "success" in result:
        console.print(f"[green]{result['success']}[/green]")
        return
    
    # Special actions
    if "action" in result:
        if result["action"] == "start_websocket":
            console.print(f"[yellow]WebSocket streaming not yet implemented[/yellow]")
        return
    
    # List results
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
    # Single dict results
    elif isinstance(result, dict):
        if "hostname" in result:
            print_agent(result)
        elif "type" in result:
            print_task(result)
        else:
            for k, v in result.items():
                console.print(f"{k}: {v}")


def print_agents(agents: list) -> None:
    """Print agents as a formatted table.
    
    Args:
        agents: List of agent objects
    """
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


def print_agent(agent: dict) -> None:
    """Print single agent details as a key-value table.
    
    Args:
        agent: Agent object
    """
    table = Table(title=f"Agent: {agent.get('id')}", show_header=False)
    for k, v in agent.items():
        if k != "id":
            table.add_row(k, str(v))
    console.print(table)


def print_tasks(tasks: list) -> None:
    """Print tasks as a formatted table.
    
    Args:
        tasks: List of task objects
    """
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


def print_task(task: dict) -> None:
    """Print single task details as a key-value table.
    
    Args:
        task: Task object
    """
    table = Table(title=f"Task: {task.get('id')}", show_header=False)
    for k, v in task.items():
        if k != "id":
            table.add_row(k, str(v))
    console.print(table)