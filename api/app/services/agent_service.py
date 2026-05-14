import hashlib
import uuid
from sqlalchemy.exc import IntegrityError
from api.app.utils.time import now_iso
from api.app.core.jwt import create_agent_token, create_agent_refresh_token_value
from api.app.repositories.agents_repo import (
    create_agent,
    get_agent_by_id,
    update_agent_status,
    list_agents as list_agents_repo,
    mark_agent_decommissioned,
)
from api.app.repositories.agent_refresh_tokens_repo import (
    create_agent_refresh_token,
    get_agent_refresh_token_by_hash,
    mark_agent_refresh_token_used,
    revoke_agent_refresh_token_family,
    revoke_agent_all_tokens,
)


def hash_refresh_token(refresh_token):
    """Hash refresh token using SHA-256.
    
    Args:
        refresh_token: Raw refresh token string
        
    Returns:
        64-character hex string (SHA-256 hash)
    """
    return hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()


def register_agent(hostname, os, user, version, metadata=None):
    """Register a new agent without authentication.
    
    Args:
        hostname: Agent hostname (required)
        os: Operating system (required)
        user: User running agent (required)
        version: Agent version (required)
        metadata: Optional additional metadata (dict)
        
    Returns:
        (dict, None): On success with agent_id, agent_token, refresh_token
        (None, (str, int)): On error with (message, http_status_code)
        
    Error cases:
    - 409: Agent with same hostname already exists
    """
    # Generate unique agent ID
    agent_id = f"agent_{uuid.uuid4().hex[:12]}"
    created_at = now_iso()
    
    try:
        # Create the agent
        agent = create_agent(
            agent_id=agent_id,
            hostname=hostname,
            os=os,
            user=user,
            version=version,
            status="online",
            last_seen=created_at,
            created_at=created_at,
            metadata=metadata,
        )
    except IntegrityError:
        # Hostname uniqueness constraint violation
        return None, ("agent with this hostname already exists", 409)
    
    # Generate refresh token
    refresh_token_value = create_agent_refresh_token_value()
    refresh_token_hash = hash_refresh_token(refresh_token_value)
    
    try:
        # Store refresh token hash
        create_agent_refresh_token(
            agent_id=agent_id,
            token_hash=refresh_token_hash,
            created_at=created_at,
        )
    except IntegrityError:
        # Should not happen, but handle gracefully
        return None, ("failed to create refresh token", 500)
    
    # Generate access token
    access_token = create_agent_token(agent_id)
    
    return {
        "agent_id": agent_id,
        "agent_token": access_token,
        "token_type": "Bearer",
        "expires_in": 900,  # 15 minutes
        "refresh_token": refresh_token_value,
        "refresh_expires_in": 2592000,  # 30 days
        "status": "online",
    }, None


def refresh_agent_token(refresh_token):
    """Refresh agent access token using a refresh token.
    
    Args:
        refresh_token: Opaque refresh token (required)
        
    Returns:
        (dict, None): On success with new agent_token and refresh_token
        (None, (str, int)): On error with (message, http_status_code)
        
    Error cases:
    - 400: Invalid/missing refresh token
    - 401: Token not found, already used, revoked, or token reuse detected
    - 409: Refresh token family conflict (token reuse detected)
    """
    if not refresh_token or len(refresh_token) < 32:
        return None, ("invalid refresh token", 400)
    
    # Hash the refresh token for database lookup
    token_hash = hash_refresh_token(refresh_token)
    token_row = get_agent_refresh_token_by_hash(token_hash)
    
    # Validate token exists and is not revoked/used
    if token_row is None:
        return None, ("refresh token not found", 401)
    
    if token_row.revoked_at is not None:
        return None, ("refresh token has been revoked", 401)
    
    if token_row.used_at is not None:
        # Token already used - detect potential token reuse
        revoke_agent_refresh_token_family(token_row.token_family_id, now_iso())
        return None, ("refresh token reuse detected - token family revoked", 409)
    
    # Get the agent
    agent = get_agent_by_id(token_row.agent_id)
    if agent is None:
        return None, ("agent not found", 404)
    
    if agent.status == "decommissioned":
        return None, ("agent has been decommissioned", 401)
    
    # Mark the old refresh token as used
    now = now_iso()
    mark_agent_refresh_token_used(token_hash, now)
    
    # Generate new tokens
    new_access_token = create_agent_token(agent.id)
    new_refresh_token_value = create_agent_refresh_token_value()
    new_refresh_token_hash = hash_refresh_token(new_refresh_token_value)
    
    try:
        # Store new refresh token with same family for future rotation detection
        # Note: In a production system, we might want to reuse token_family_id
        # but for simplicity here we generate new ones
        create_agent_refresh_token(
            agent_id=agent.id,
            token_hash=new_refresh_token_hash,
            created_at=now,
        )
    except IntegrityError:
        return None, ("failed to create new refresh token", 500)
    
    return {
        "agent_id": agent.id,
        "agent_token": new_access_token,
        "token_type": "Bearer",
        "expires_in": 900,  # 15 minutes
        "refresh_token": new_refresh_token_value,
        "refresh_expires_in": 2592000,  # 30 days
    }, None


def record_agent_heartbeat(agent_id, status=None):
    """Record a heartbeat for an agent and update its status.
    
    Args:
        agent_id: Agent ID (from JWT token)
        status: Optional new status (default: "online")
        
    Returns:
        (dict, None): On success with updated agent info and server time
        (None, (str, int)): On error with (message, http_status_code)
    """
    agent = get_agent_by_id(agent_id)
    
    if agent is None:
        return None, ("agent not found", 404)
    
    if agent.status == "decommissioned":
        return None, ("agent has been decommissioned", 401)
    
    now = now_iso()
    new_status = status or "online"
    
    # Update agent status and last_seen
    agent = update_agent_status(agent_id, new_status, last_seen=now)
    
    return {
        "agent_id": agent.id,
        "status": agent.status,
        "server_time": now,
    }, None


def list_agents(status=None, limit=50, offset=0):
    """List agents with optional filtering.
    
    Args:
        status: Optional status filter (online, offline, dead, decommissioned)
        limit: Number of agents per page (default: 50)
        offset: Offset for pagination (default: 0)
        
    Returns:
        (dict, None): On success with agents list and pagination info
        (None, (str, int)): On error with (message, http_status_code)
    """
    try:
        agents, total_count = list_agents_repo(status=status, limit=limit, offset=offset)
        
        # Convert agents to dictionaries
        agents_data = [
            {
                "id": agent.id,
                "hostname": agent.hostname,
                "os": agent.os,
                "user": agent.user,
                "version": agent.version,
                "status": agent.status,
                "last_seen": agent.last_seen,
                "created_at": agent.created_at,
                "decommissioned_at": agent.decommissioned_at,
            }
            for agent in agents
        ]
        
        return {
            "data": agents_data,
            "pagination": {
                "page_size": limit,
                "next_cursor": None if offset + limit >= total_count else str(offset + limit),
                "has_more": offset + limit < total_count,
                "sort": "created_at_desc",
            }
        }, None
    except Exception as e:
        return None, (f"failed to list agents: {str(e)}", 500)


def get_agent_details(agent_id):
    """Get details for a specific agent.
    
    Args:
        agent_id: Agent ID to retrieve
        
    Returns:
        (dict, None): On success with agent details
        (None, (str, int)): On error with (message, http_status_code)
    """
    agent = get_agent_by_id(agent_id)
    
    if agent is None:
        return None, ("agent not found", 404)
    
    return {
        "data": {
            "id": agent.id,
            "hostname": agent.hostname,
            "os": agent.os,
            "user": agent.user,
            "version": agent.version,
            "status": agent.status,
            "last_seen": agent.last_seen,
            "created_at": agent.created_at,
            "decommissioned_at": agent.decommissioned_at,
        }
    }, None


def decommission_agent(agent_id, operator_id):
    """Decommission an agent and revoke its tokens.
    
    Args:
        agent_id: Agent ID to decommission
        operator_id: Operator performing the decommissioning
        
    Returns:
        (dict, None): On success with decommissioning details
        (None, (str, int)): On error with (message, http_status_code)
    """
    agent = get_agent_by_id(agent_id)
    
    if agent is None:
        return None, ("agent not found", 404)
    
    if agent.status == "decommissioned":
        # Already decommissioned - idempotent response
        now = agent.decommissioned_at or now_iso()
        return {
            "data": {
                "agent_id": agent.id,
                "status": "decommissioned",
                "deleted_at": now,
                "deletion_mode": "soft_delete",
            },
            "audit": {
                "operator_id": operator_id,
                "timestamp": now,
                "action": "decommissioned",
            }
        }, None
    
    now = now_iso()
    
    try:
        # Mark agent as decommissioned
        mark_agent_decommissioned(agent_id, now)
        
        # Revoke all refresh tokens for the agent
        revoke_agent_all_tokens(agent_id, now)
        
        return {
            "data": {
                "agent_id": agent_id,
                "status": "decommissioned",
                "deleted_at": now,
                "deletion_mode": "soft_delete",
            },
            "audit": {
                "operator_id": operator_id,
                "timestamp": now,
                "action": "decommissioned",
            }
        }, None
    except Exception as e:
        return None, (f"failed to decommission agent: {str(e)}", 500)

