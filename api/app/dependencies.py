from functools import wraps

from flask import request

from api.app.core.jwt import verify_operator_token
from api.app.schemas.errors import APIError


def require_operator_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            raise APIError(code="UNAUTHORIZED", message="Missing or invalid token", status=401)

        token = auth_header.replace("Bearer ", "", 1).strip()
        payload = verify_operator_token(token)

        if payload is None:
            raise APIError(code="UNAUTHORIZED", message="Invalid or expired token", status=401)

        return func(*args, **kwargs)

    return wrapper