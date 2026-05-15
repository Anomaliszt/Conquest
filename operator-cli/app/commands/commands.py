"""Command parser and dispatcher.

Routes user input to appropriate handler functions.
"""

from app.core.config import get_server
from app.api.client import APIClient
from app.api.auth import login as api_login
from app.core.config import save_credentials, load_credentials
from app.commands.handlers import login, register, logout, status, show, run, cancel, help, clear


def _refresh_token(ctx, server):
    """Attempt to refresh the JWT token using stored credentials.
    
    Called automatically when API returns 401 (token expired).
    
    Args:
        ctx: CLI context with token and credentials
        server: C2 server URL
    
    Returns:
        True if refresh succeeded, False otherwise
    """
    creds = load_credentials()
    if creds and creds.get("username") and creds.get("password"):
        try:
            token, expires = api_login(server, creds["username"], creds["password"])
            save_credentials(token, creds["username"], creds["password"])
            ctx["token"] = token
            print(f"Token refreshed")
            return True
        except:
            pass
    return False


def parse_command(cmd: str, ctx: dict) -> dict:
    """Parse user input and dispatch to appropriate handler.
    
    Args:
        cmd: Raw command string from user
        ctx: CLI context with config, token, authentication state
    
    Returns:
        Result dict to be formatted and displayed
    """
    parts = cmd.strip().split()
    if not parts:
        return None
    
    config = ctx["config"]
    server = get_server(config)
    
    # Setup token refresh callback for the API client
    def on_token_expired():
        _refresh_token(ctx, server)
    
    # Create API client with token support and refresh handling.
    api = APIClient(server, ctx.get("token"), on_token_expired)
    
    cmd_lower = parts[0].lower()
    
    # Route to appropriate handler
    if cmd_lower == "login":
        return login(parts, ctx, server)
    
    if cmd_lower == "register":
        return register(parts, ctx, server)
    
    if cmd_lower == "logout":
        return logout(ctx)
    
    if cmd_lower == "help":
        return help()
    
    if cmd_lower == "show" and len(parts) >= 2:
        return show(parts, api)
    
    if cmd_lower == "run" and len(parts) >= 4:
        return run(parts, api)
    
    if cmd_lower == "cancel" and len(parts) >= 2:
        return cancel(parts, api)
    
    if cmd_lower == "status":
        return status(ctx, server)
    
    if cmd_lower == "clear":
        return clear()
    
    return {"error": f"Unknown command: {cmd_lower}. Type 'help' for available commands."}