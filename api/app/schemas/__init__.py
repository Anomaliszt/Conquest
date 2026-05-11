"""Pydantic schemas for the Conquest API."""

from .operator import (
    RegisterOperatorRequest,
    LoginOperatorRequest,
    RegisterOperatorResponse,
    LoginOperatorResponse,
)
from .agent import (
    RegisterAgentRequest,
    RegisterAgentResponse,
    RefreshAgentTokenRequest,
    RefreshAgentTokenResponse,
    AgentHeartbeatRequest,
    AgentHeartbeatResponse,
    Agent,
    AgentResponse,
    AgentListResponse,
    DeleteAgentResponse,
)
from .errors import (
    ErrorResponse,
    ErrorDetail,
    ValidationErrorDetail,
)

__all__ = [
    "RegisterOperatorRequest",
    "LoginOperatorRequest",
    "RegisterOperatorResponse",
    "LoginOperatorResponse",
    "RegisterAgentRequest",
    "RegisterAgentResponse",
    "RefreshAgentTokenRequest",
    "RefreshAgentTokenResponse",
    "AgentHeartbeatRequest",
    "AgentHeartbeatResponse",
    "Agent",
    "AgentResponse",
    "AgentListResponse",
    "DeleteAgentResponse",
    "ErrorResponse",
    "ErrorDetail",
    "ValidationErrorDetail",
]