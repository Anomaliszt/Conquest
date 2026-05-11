"""Pydantic schemas for agent registration, token refresh, and management endpoints."""

from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, Any, List
from datetime import datetime


class RegisterAgentRequest(BaseModel):
    """Request schema for agent registration endpoint.
    
    Validates that:
    - hostname: 1-255 characters
    - os: 1-100 characters
    - user: 1-255 characters
    - version: 1-50 characters
    - metadata: optional additional properties
    
    This endpoint requires no authentication or registration token.
    """
    hostname: str = Field(
        ..., 
        min_length=1, 
        max_length=255,
        description="Agent hostname"
    )
    os: str = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="Operating system (e.g., 'windows', 'linux')"
    )
    user: str = Field(
        ..., 
        min_length=1, 
        max_length=255,
        description="User running the agent"
    )
    version: str = Field(
        ..., 
        min_length=1, 
        max_length=50,
        description="Agent version"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        max_length=50,
        description="Optional additional agent metadata"
    )


class RegisterAgentResponse(BaseModel):
    """Response schema for successful agent registration (HTTP 201)."""
    data: "RegisterAgentTokenData" = Field(..., description="Agent registration data")


class RegisterAgentTokenData(BaseModel):
    """Token data returned in agent registration response."""
    agent_id: str = Field(..., description="Unique agent ID (format: agent_<random>)")
    agent_token: str = Field(..., description="JWT access token")
    token_type: Literal["Bearer"] = Field(..., description="Type of token (Bearer)")
    expires_in: int = Field(..., description="Access token expiration time in seconds (900 = 15 minutes)")
    refresh_token: str = Field(..., description="Opaque single-use refresh token")
    refresh_expires_in: int = Field(..., description="Refresh token expiration time in seconds (2592000 = 30 days)")
    status: Literal["online"] = Field(..., description="Initial agent status")


class RefreshAgentTokenRequest(BaseModel):
    """Request schema for agent token refresh endpoint.
    
    Validates that:
    - refresh_token: 32-4096 characters (opaque token issued during registration or previous refresh)
    """
    refresh_token: str = Field(
        ..., 
        min_length=32, 
        max_length=4096,
        description="Opaque refresh token. Single-use only. Reuse is detected and causes token family revocation."
    )


class RefreshAgentTokenResponse(BaseModel):
    """Response schema for successful token refresh (HTTP 200)."""
    data: "RefreshAgentTokenData" = Field(..., description="Refreshed token data")


class RefreshAgentTokenData(BaseModel):
    """Token data returned in refresh response."""
    agent_id: str = Field(..., description="Agent ID")
    agent_token: str = Field(..., description="New JWT access token")
    token_type: Literal["Bearer"] = Field(..., description="Type of token (Bearer)")
    expires_in: int = Field(..., description="Access token expiration time in seconds (900 = 15 minutes)")
    refresh_token: str = Field(..., description="New rotated refresh token")
    refresh_expires_in: int = Field(..., description="Refresh token expiration time in seconds (2592000 = 30 days)")


class AgentHeartbeatRequest(BaseModel):
    """Request schema for agent heartbeat endpoint.
    
    Both fields are optional. If status is not provided, defaults to "online".
    """
    status: Optional[Literal["online"]] = Field(
        None,
        description="Current agent liveness status"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        max_length=50,
        description="Optional heartbeat metadata"
    )


class AgentHeartbeatResponse(BaseModel):
    """Response schema for successful heartbeat (HTTP 200)."""
    data: "AgentHeartbeatData" = Field(..., description="Heartbeat response data")


class AgentHeartbeatData(BaseModel):
    """Heartbeat data returned in response."""
    agent_id: str = Field(..., description="Agent ID")
    status: str = Field(..., description="Accepted agent status")
    server_time: str = Field(..., description="Server time in ISO 8601 format")


class Agent(BaseModel):
    """Agent entity returned in list and detail responses."""
    id: str = Field(..., description="Unique agent ID (format: agent_<random>)")
    hostname: str = Field(..., description="Agent hostname")
    os: str = Field(..., description="Operating system")
    user: str = Field(..., description="User running the agent")
    version: str = Field(..., description="Agent version")
    status: Literal["online", "offline", "dead", "decommissioned"] = Field(..., description="Agent status")
    last_seen: str = Field(..., description="ISO timestamp of last heartbeat")
    created_at: str = Field(..., description="ISO timestamp of agent creation")
    decommissioned_at: Optional[str] = Field(None, description="ISO timestamp of decommissioning")


class AgentResponse(BaseModel):
    """Response schema for get agent details endpoint (HTTP 200)."""
    data: Agent = Field(..., description="Agent details")


class CursorPagination(BaseModel):
    """Cursor pagination metadata."""
    page_size: int = Field(..., description="Number of items per page")
    next_cursor: Optional[str] = Field(None, description="Cursor for next page")
    has_more: bool = Field(..., description="Whether there are more items")
    sort: str = Field(..., description="Sort order applied")


class AgentListResponse(BaseModel):
    """Response schema for list agents endpoint (HTTP 200)."""
    data: List[Agent] = Field(..., description="List of agents")
    pagination: CursorPagination = Field(..., description="Pagination metadata")


class AuditInfo(BaseModel):
    """Audit information for state-changing operations."""
    operator_id: Optional[str] = Field(None, description="Operator who performed the action")
    timestamp: str = Field(..., description="Action timestamp")
    action: str = Field(..., description="Action performed (e.g., 'decommissioned')")


class DeleteAgentResponse(BaseModel):
    """Response schema for decommission agent endpoint (HTTP 202)."""
    data: "DeleteAgentData" = Field(..., description="Decommissioning result")
    audit: AuditInfo = Field(..., description="Audit information")


class DeleteAgentData(BaseModel):
    """Data returned when decommissioning an agent."""
    agent_id: str = Field(..., description="Agent ID")
    status: Literal["decommissioned"] = Field(..., description="New agent status")
    deleted_at: str = Field(..., description="ISO timestamp of decommissioning")
    deletion_mode: Literal["soft_delete"] = Field(..., description="Deletion mode")
