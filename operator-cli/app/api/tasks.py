"""Client for task-related API operations."""

from app.api.client import APIClient


class TasksClient:
    """Client for managing tasks via the C2 REST API."""
    
    def __init__(self, client: APIClient):
        self._client = client
    
    def list(self, agent_id: str = None, status: str = None) -> list:
        """List tasks, optionally filtered by agent and/or status.
        
        Args:
            agent_id: Optional filter by agent ID
            status: Optional filter - "queued", "dispatched", "running", 
                   "completed", "failed", "cancelled", "orphaned"
        
        Returns:
            List of task objects
        """
        params = {}  # Build optional query parameters for the list endpoint
        if agent_id:
            params["agent_id"] = agent_id
        if status:
            params["status"] = status
        resp = self._client._request("GET", "/api/v1/tasks", params=params)
        return resp.json()["data"]
    
    def get(self, task_id: str) -> dict:
        """Get details of a specific task.
        
        Args:
            task_id: The task identifier (e.g., "task_abc123")
        
        Returns:
            Task object with details
        """
        resp = self._client._request("GET", f"/api/v1/tasks/{task_id}")
        return resp.json()["data"]
    
    def result(self, task_id: str) -> dict:
        """Get the result of a completed task.
        
        Args:
            task_id: The task identifier
        
        Returns:
            Task result object with stdout, stderr, exit_code
        """
        resp = self._client._request("GET", f"/api/v1/tasks/{task_id}/result")
        return resp.json()["data"]
    
    def cancel(self, task_id: str) -> dict:
        """Request cancellation of a task.
        
        Args:
            task_id: The task identifier
        
        Returns:
            Cancellation confirmation
        """
        resp = self._client._request("POST", f"/api/v1/tasks/{task_id}/cancel")
        return resp.json()["data"]
    
    def create(self, agent_id: str, command: str, payload: dict = None) -> dict:
        """Create a new task for an agent.
        
        Args:
            agent_id: Target agent identifier
            command: Command type - "whoami", "uptime", "shell_execute"
            payload: Optional command-specific payload
        
        Returns:
            Created task object
        """
        data = {"type": command, "payload": payload or {}}
        resp = self._client._request(
            "POST",
            f"/api/v1/agents/{agent_id}/tasks",
            json=data
        )
        return resp.json()["data"]