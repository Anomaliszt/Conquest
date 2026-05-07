import jwt
from datetime import timedelta, timezone
from api.app.utils.time import time_now

from api.app.config import SECRET_KEY


def create_operator_token(operator_id):
    """Creates a JWT token for the given operator ID with a 15-minute expiration."""
    now = time_now()

    payload = {
        "sub": operator_id,
        "scope": "operator",
        "iat": now,
        "exp": now + timedelta(minutes=15),
    }

    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def verify_operator_token(token):
    """Verifies the given JWT token and returns the payload if valid, or None if invalid or expired."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None

    if payload.get("scope") != "operator":
        return None

    return payload