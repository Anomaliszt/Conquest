from functools import wraps

from flask import request

from api.app.core.jwt import verify_operator_token, verify_agent_token
from api.app.schemas.errors import APIError


def require_operator_auth(func):
    """Decorator to require valid operator JWT token.
    
    Extracts and validates the operator JWT from the Authorization header.
    If valid, adds operator_id to the function kwargs.
    If invalid or missing, raises 401 error.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            raise APIError(
                code="UNAUTHORIZED",
                message="Missing or invalid authorization header",
                status=401
            )

        token = auth_header[7:]  # Remove "Bearer " prefix
        payload = verify_operator_token(token)

        if payload is None:
            raise APIError(
                code="UNAUTHORIZED",
                message="Invalid or expired operator token",
                status=401
            )

        kwargs['operator_id'] = payload.get("sub")
        return func(*args, **kwargs)

    return wrapper


def require_agent_auth(func):
    """Decorator to require valid agent JWT token.
    
    Extracts and validates the agent JWT from the Authorization header.
    If valid, adds agent_id to the function kwargs.
    If invalid or missing, raises 401 error.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            raise APIError(
                code="UNAUTHORIZED",
                message="Missing or invalid authorization header",
                status=401
            )

        token = auth_header[7:]  # Remove "Bearer " prefix
        payload = verify_agent_token(token)

        if payload is None:
            raise APIError(
                code="UNAUTHORIZED",
                message="Invalid or expired agent token",
                status=401
            )

        kwargs['agent_id'] = payload.get("sub")
        return func(*args, **kwargs)

    return wrapper