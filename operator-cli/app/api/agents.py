"""Client for agent-related API operations."""

from app.api.client import APIClient


class AgentsClient:
    """Client for managing agents via the C2 REST API."""
    
    def __init__(self, client: APIClient):
        self._client = client
    
    def list(self, status: str = None) -> list:
        """List all registered agents, optionally filtered by status.
        
        Args:
            status: Optional filter - "online", "offline", "dead", "decommissioned"
        
        Returns:
            List of agent objects
        """
        params = {"status": status} if status else {}  # Optional status filter for agents
        resp = self._client._request("GET", "/api/v1/agents", params=params)
        return resp.json()["data"]
    
    def get(self, agent_id: str) -> dict:
        """Get details of a specific agent.
        
        Args:
            agent_id: The agent identifier (e.g., "agent_001")
        
        Returns:
            Agent object with details
        """
        resp = self._client._request("GET", f"/api/v1/agents/{agent_id}")
        return resp.json()["data"]