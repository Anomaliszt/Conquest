"""HTTP client for the Conquest C2 server."""

import requests


class APIClient:
    """Main HTTP client for communicating with the C2 server.
    
    Provides:
    - Request execution with authentication headers
    - Automatic token refresh on 401 responses
    - Lazy-loaded sub-clients for agents and tasks endpoints
    """
    
    def __init__(self, server, token=None, on_token_expired=None):
        self.server = server
        self.token = token
        self._on_token_expired = on_token_expired  # Callback for token refresh
    
    def _headers(self):
        """Build request headers including authentication token."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            # Include bearer token when available for authenticated requests.
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def _request(self, method, path, **kwargs):
        """Execute HTTP request with automatic token refresh on 401."""
        url = f"{self.server}{path}"
        resp = requests.request(method, url, headers=self._headers(), **kwargs)
        
        # Attempt token refresh if request failed with 401
        if resp.status_code == 401 and self._on_token_expired:
            self._on_token_expired()
            resp = requests.request(method, url, headers=self._headers(), **kwargs)
        
        resp.raise_for_status()
        return resp
    
    @property
    def agents(self):
        """Lazy-loaded client for agent operations."""
        from app.api.agents import AgentsClient
        return AgentsClient(self)
    
    @property
    def tasks(self):
        """Lazy-loaded client for task operations."""
        from app.api.tasks import TasksClient
        return TasksClient(self)