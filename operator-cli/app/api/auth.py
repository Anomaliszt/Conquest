import requests

def _parse_error(resp):
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
    except:
        pass
    return f"HTTP {resp.status_code}"

def register(server, registration_token, username, password):
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

def login(server, username, password):
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