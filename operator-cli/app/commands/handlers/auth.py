import getpass
from app.api.auth import login as api_login, register as api_register
from app.core.config import save_credentials

def register(parts, ctx, server):
    if len(parts) >= 4:
        token = parts[1]
        username = parts[2]
        password = parts[3]
    else:
        print("Registration requires: register <token> <username> <password>")
        token = input("Registration token: ")
        username = input("Username: ")
        password = getpass.getpass("Password: ")
        if not token or not username or not password:
            return {"error": "Missing required fields"}
    
    try:
        api_register(server, token, username, password)
        return {"success": f"Registered as {username}. Now run 'login' to authenticate."}
    except Exception as e:
        return {"error": str(e)}

def login(parts, ctx, server):
    if len(parts) >= 3:
        username = parts[1]
        password = parts[2]
    else:
        username = input("Username: ")
        password = getpass.getpass("Password: ")
    
    try:
        token, expires = api_login(server, username, password)
        save_credentials(token, username, password)
        ctx["token"] = token
        ctx["authenticated"] = True
        ctx["username"] = username
        ctx["password"] = password
        return {"success": f"Logged in as {username} (expires in {expires}s)"}
    except Exception as e:
        return {"error": str(e)}

def logout(ctx):
    import os
    creds_path = os.path.expanduser("~/.conquest/credentials.json")
    if os.path.exists(creds_path):
        os.remove(creds_path)
    ctx["token"] = None
    ctx["authenticated"] = False
    ctx["username"] = None
    return {"success": "Logged out"}

def status(ctx, server):
    username = ctx.get("username", "not logged in")
    authenticated = ctx.get("authenticated", False)
    token = ctx.get("token", "")
    
    return {
        "server": server,
        "logged_in": username,
        "authenticated": authenticated,
        "token_present": bool(token)
    }