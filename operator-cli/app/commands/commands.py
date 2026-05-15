from app.core.config import get_server
from app.api.client import APIClient
from app.api.auth import login as api_login
from app.core.config import save_credentials, load_credentials
from app.commands.handlers import login, register, logout, status, show, run, cancel, help, clear

def _refresh_token(ctx, server):
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

def parse_command(cmd, ctx):
    parts = cmd.strip().split()
    if not parts:
        return None
    
    config = ctx["config"]
    server = get_server(config)
    
    def on_token_expired():
        _refresh_token(ctx, server)
    
    api = APIClient(server, ctx.get("token"), on_token_expired)
    
    cmd_lower = parts[0].lower()
    
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