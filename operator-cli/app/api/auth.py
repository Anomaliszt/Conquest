"""Authentication functions for operator login and registration."""

import requests


def _parse_error(resp):
    """Parse API error response into human-readable message.
    
    Extracts error code, message, and validation details from API responses.
    """
    try:
        data = resp.json()
        if "error" in data:
            error = data["error"]
            msg = error.get("message", "")
            if "details" in error:
                details = error["details"]
                if details:
                    first_detail = details[0]
                    return f"{msg}: {first_detail.get('reason', msg)}"
            return msg
    except Exception:
        # If the response body is not valid JSON, fall back to the HTTP status.
        pass
    return f"HTTP {resp.status_code}"


def register(server: str, registration_token: str, username: str, password: str) -> dict:
    """Register a new operator account.
    
    Args:
        server: C2 server base URL
        registration_token: One-time registration token
        username: Desired username (3-100 chars, alphanumeric with ._-)
        password: Desired password (minimum 12 characters)
    
    Returns:
        Created operator data
    
    Raises:
        Exception: On validation error (400), invalid token (409), or server error
    """
    resp = requests.post(f"{server}/api/v1/operator/register", json={
        "registration_token": registration_token,
        "username": username,
        "password": password
    })
    if resp.status_code == 201:
        return resp.json()["data"]
    elif resp.status_code in (400, 401, 409):
        raise Exception(_parse_error(resp))
    else:
        raise Exception(f"Registration failed: {resp.status_code}")


def login(server: str, username: str, password: str) -> tuple:
    """Authenticate an operator and obtain an access token.
    
    Args:
        server: C2 server base URL
        username: Operator username
        password: Operator password
    
    Returns:
        Tuple of (operator_token, expires_in_seconds)
    
    Raises:
        Exception: On invalid credentials (401) or server error
    """
    resp = requests.post(f"{server}/api/v1/operator/login", json={
        "username": username,
        "password": password
    })
    if resp.status_code == 200:
        data = resp.json()["data"]
        return data.get("operator_token", data.get("token")), data.get("expires_in", 900)
    elif resp.status_code in (400, 401):
        raise Exception(_parse_error(resp))
    else:
        raise Exception(f"Login failed: {resp.status_code}")