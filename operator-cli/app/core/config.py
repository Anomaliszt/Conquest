import os
import json

CONFIG_PATH = os.path.expanduser("~/.conquest/config.json")
CREDS_PATH = os.path.expanduser("~/.conquest/credentials.json")

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {"server": "http://localhost:8000", "current": "default"}

def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

def get_server(config):
    current = config.get("current", "default")
    contexts = config.get("contexts", {})
    if current in contexts:
        return contexts[current].get("server", "http://localhost:8000")
    return config.get("server", "http://localhost:8000")

def save_credentials(token, username, password=None):
    os.makedirs(os.path.dirname(CREDS_PATH), exist_ok=True)
    data = {"username": username, "token": token}
    if password:
        data["password"] = password
    with open(CREDS_PATH, "w") as f:
        json.dump(data, f)

def load_credentials():
    if os.path.exists(CREDS_PATH):
        with open(CREDS_PATH) as f:
            return json.load(f)
    return None