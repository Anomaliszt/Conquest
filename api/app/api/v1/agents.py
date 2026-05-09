from flask import Blueprint, request

from api.app.schemas.errors import APIError
from api.app.services.agent_service import (
    list_agents,
    get_agent_details,
    decommission_agent,
)
from api.app.schemas import (
    AgentListResponse,
    AgentResponse,
    DeleteAgentResponse,
)
from api.app.dependencies import require_operator_auth

agents_bp = Blueprint("agents", __name__)


@agents_bp.get("")
@require_operator_auth
def list_agents_route(operator_id):
    """List agents with optional filtering.
    
    Query Parameters:
    - status: Filter by status (online, offline, dead, decommissioned)
    - page_size: Items per page (default: 50, max: 1000)
    - page_cursor: Cursor for pagination
    
    Requires operator authentication.
    
    HTTP Responses:
    - 200: Agents list returned
    - 400: Invalid query parameters
    - 401: Missing or invalid operator token
    - 403: Insufficient permissions
    - 429: Rate limited
    """
    status = request.args.get("status")
    try:
        page_size = int(request.args.get("page_size", 50))
        page_size = min(page_size, 1000)  # Max 1000
    except (ValueError, TypeError):
        raise APIError(
            code="BAD_REQUEST",
            message="Invalid page_size parameter",
            status=400
        )
    
    try:
        page_cursor = int(request.args.get("page_cursor", 0))
    except (ValueError, TypeError):
        page_cursor = 0
    
    result, error = list_agents(status=status, limit=page_size, offset=page_cursor)
    
    if error:
        message, status_code = error
        raise APIError(
            code="INTERNAL_ERROR",
            message=message,
            status=status_code
        )
    
    return AgentListResponse(**result).model_dump(), 200


@agents_bp.get("/<agent_id>")
@require_operator_auth
def get_agent_route(agent_id, operator_id):
    """Get details for a specific agent.
    
    Requires operator authentication.
    
    HTTP Responses:
    - 200: Agent details returned
    - 401: Missing or invalid operator token
    - 403: Insufficient permissions
    - 404: Agent not found
    - 429: Rate limited
    """
    result, error = get_agent_details(agent_id)
    
    if error:
        message, status_code = error
        raise APIError(
            code="NOT_FOUND" if status_code == 404 else "INTERNAL_ERROR",
            message=message,
            status=status_code
        )
    
    return AgentResponse(**result).model_dump(), 200


@agents_bp.delete("/<agent_id>")
@require_operator_auth
def decommission_agent_route(agent_id, operator_id):
    """Decommission an agent.
    
    Decommissions an agent, revokes its access tokens and refresh tokens,
    and cancels queued tasks. Running tasks become orphaned after the
    configured offline timeout.
    
    Requires operator authentication.
    
    HTTP Responses:
    - 202: Decommissioning accepted
    - 401: Missing or invalid operator token
    - 403: Insufficient permissions
    - 404: Agent not found
    - 429: Rate limited
    """
    result, error = decommission_agent(agent_id, operator_id)
    
    if error:
        message, status_code = error
        error_code_map = {
            404: "NOT_FOUND",
            500: "INTERNAL_ERROR"
        }
        raise APIError(
            code=error_code_map.get(status_code, "INTERNAL_ERROR"),
            message=message,
            status=status_code
        )
    
    return DeleteAgentResponse(**result).model_dump(), 202
