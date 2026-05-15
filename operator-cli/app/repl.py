import os
import readline
from app.core.config import load_config, load_credentials
from app.commands import parse_command
from app.formatters import print_result

def run_repl():
    config = load_config()
    creds = load_credentials()
    
    ctx = {
        "config": config,
        "authenticated": False,
        "token": None,
        "username": None,
        "password": None,
    }
    
    if creds and creds.get("token"):
        ctx["token"] = creds.get("token")
        ctx["username"] = creds.get("username")
        ctx["password"] = creds.get("password")
        ctx["authenticated"] = True
    
    print(f"Conquest v0.1.0 - Operator CLI")
    print(f"Server: {config.get('server', 'http://localhost:8000')}")
    if ctx.get("authenticated"):
        print(f"Logged in as: {ctx.get('username')}")
    else:
        print('Type "login" or "help" to get started')
    print()
    
    while True:
        try:
            prompt = get_prompt(ctx)
            cmd = input(prompt).strip()
            
            if not cmd:
                continue
            if cmd in ("exit", "quit", "logout"):
                print("Goodbye!")
                break
            
            result = parse_command(cmd, ctx)
            handle_result(result, ctx)
            
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\n(Use 'exit' to quit)")
            
def get_prompt(ctx):
    if ctx.get("authenticated"):
        return f"conquest> "
    return "conquest (not logged in)> "

def handle_result(result, ctx):
    if result is None:
        return
    
    if isinstance(result, dict) and result.get("action") == "clear":
        os.system("clear" if os.name == "posix" else "cls")
        return
    
    print_result(result, ctx)