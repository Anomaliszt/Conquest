"""Configuration and credential management for the CLI.

Handles:
- Server configuration (multi-context support)
- Credential storage for persistent authentication
"""

import os
import json


# Configuration file paths
CONFIG_PATH = os.path.expanduser("~/.conquest/config.json")
CREDS_PATH = os.path.expanduser("~/.conquest/credentials.json")


def load_config() -> dict:
    """Load CLI configuration from disk.
    
    Returns:
        Configuration dict with server URL and context settings.
        Defaults to localhost:8000 if config file doesn't exist.
    """
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {"server": "http://localhost:8000", "current": "default"}


def save_config(config: dict) -> None:
    """Save CLI configuration to disk.
    
    Args:
        config: Configuration dictionary to serialize
    """
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    # Ensure the configuration directory exists before saving.
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def get_server(config: dict) -> str:
    """Get the current server URL from configuration.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        Server base URL, defaulting to localhost:8000
    """
    current = config.get("current", "default")
    contexts = config.get("contexts", {})
    if current in contexts:
        return contexts[current].get("server", "http://localhost:8000")
    return config.get("server", "http://localhost:8000")


def save_credentials(token: str, username: str, password: str = None) -> None:
    """Save operator credentials for persistent authentication.
    
    Stores username, JWT token, and optionally password for auto-refresh.
    
    Args:
        token: JWT access token
        username: Operator username
        password: Optional password for token refresh
    """
    os.makedirs(os.path.dirname(CREDS_PATH), exist_ok=True)
    data = {"username": username, "token": token}
    if password:
        data["password"] = password
    with open(CREDS_PATH, "w") as f:
        json.dump(data, f)


def load_credentials() -> dict | None:
    """Load stored operator credentials.
    
    Returns:
        Credentials dict with username, token, and optionally password,
        or None if credentials file doesn't exist.
    """
    if os.path.exists(CREDS_PATH):
        with open(CREDS_PATH) as f:
            return json.load(f)
    return None