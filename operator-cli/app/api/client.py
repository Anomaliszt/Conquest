import requests

class APIClient:
    def __init__(self, server, token=None, on_token_expired=None):
        self.server = server
        self.token = token
        self._on_token_expired = on_token_expired
    
    def _headers(self):
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def _request(self, method, path, **kwargs):
        url = f"{self.server}{path}"
        resp = requests.request(method, url, headers=self._headers(), **kwargs)
        
        if resp.status_code == 401 and self._on_token_expired:
            self._on_token_expired()
            resp = requests.request(method, url, headers=self._headers(), **kwargs)
        
        resp.raise_for_status()
        return resp
    
    @property
    def agents(self):
        from app.api.agents import AgentsClient
        return AgentsClient(self)
    
    @property
    def tasks(self):
        from app.api.tasks import TasksClient
        return TasksClient(self)