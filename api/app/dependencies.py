from functools import wraps

from flask import request, jsonify

from api.app.core.jwt import verify_operator_token


def require_operator_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "missing bearer token"}), 401

        token = auth_header.replace("Bearer ", "", 1).strip()
        payload = verify_operator_token(token)

        if payload is None:
            return jsonify({"error": "invalid or expired token"}), 401

        return func(*args, **kwargs)

    return wrapper