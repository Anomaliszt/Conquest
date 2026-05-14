from flask import Blueprint, request

from api.app.schemas.errors import APIError
from api.app.services.agent_service import (
    register_agent,
    refresh_agent_token,
    record_agent_heartbeat,
)
from api.app.core.jwt import verify_agent_token, verify_operator_token
from api.app.schemas import (
    RegisterAgentRequest,
    RegisterAgentResponse,
    RefreshAgentTokenRequest,
    RefreshAgentTokenResponse,
    AgentHeartbeatRequest,
    AgentHeartbeatResponse,
)
from api.app.dependencies import require_agent_auth, require_operator_auth

agent_auth_bp = Blueprint("agent_auth", __name__)


@agent_auth_bp.post("/register")
def register_agent_route():
    """Register a new agent without authentication.
    
    Any client that can reach this endpoint and submits a valid registration payload
    can create an agent record and receive tokens. Network reachability is the only
    registration boundary.
    
    HTTP Responses:
    - 201: Agent successfully registered
    - 400: Validation error or malformed request
    - 409: Agent with same hostname already exists
    - 429: Rate limited
    """
    data = RegisterAgentRequest(**request.get_json())

    result, error = register_agent(
        hostname=data.hostname,
        os=data.os,
        user=data.user,
        version=data.version,
        metadata=data.metadata,
    )

    if error:
        message, status_code = error
        error_code_map = {409: "CONFLICT", 500: "INTERNAL_ERROR"}
        raise APIError(
            code=error_code_map.get(status_code, "INTERNAL_ERROR"),
            message=message,
            status=status_code
        )

    return RegisterAgentResponse(data=result).model_dump(), 201


@agent_auth_bp.post("/token/refresh")
def refresh_agent_token_route():
    """Refresh agent access token using a refresh token.
    
    Exchanges a valid refresh token for a new access token and rotated refresh token.
    Refresh tokens are single-use; reuse is detected and causes token family revocation.
    
    HTTP Responses:
    - 200: Token refresh successful
    - 400: Invalid or missing refresh token
    - 401: Token not found, expired, or reused (revokes token family)
    - 404: Agent not found
    - 409: Token reuse detected (token family revoked)
    - 429: Rate limited
    """
    data = RefreshAgentTokenRequest(**request.get_json())

    result, error = refresh_agent_token(refresh_token=data.refresh_token)

    if error:
        message, status_code = error
        error_code_map = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            404: "NOT_FOUND",
            409: "CONFLICT",
            500: "INTERNAL_ERROR"
        }
        raise APIError(
            code=error_code_map.get(status_code, "INTERNAL_ERROR"),
            message=message,
            status=status_code
        )

    return RefreshAgentTokenResponse(data=result).model_dump(), 200


@agent_auth_bp.post("/heartbeat")
@require_agent_auth
def agent_heartbeat_route(agent_id):
    """Record an agent heartbeat.
    
    Updates the agent's last_seen timestamp and optionally updates its status.
    Requires valid agent JWT token in Authorization header.
    
    HTTP Responses:
    - 200: Heartbeat recorded successfully
    - 400: Validation error
    - 401: Missing or invalid agent token
    - 404: Agent not found
    - 429: Rate limited
    """
    # Request body is optional
    request_data = request.get_json() or {}
    data = AgentHeartbeatRequest(**request_data)

    result, error = record_agent_heartbeat(agent_id=agent_id, status=data.status)

    if error:
        message, status_code = error
        error_code_map = {
            401: "UNAUTHORIZED",
            404: "NOT_FOUND",
            500: "INTERNAL_ERROR"
        }
        raise APIError(
            code=error_code_map.get(status_code, "INTERNAL_ERROR"),
            message=message,
            status=status_code
        )

    return AgentHeartbeatResponse(data=result).model_dump(), 200
