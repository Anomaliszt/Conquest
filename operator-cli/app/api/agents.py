class AgentsClient:
    def __init__(self, client):
        self._client = client
    
    def list(self, status=None):
        params = {"status": status} if status else {}
        resp = self._client._request("GET", "/api/v1/agents", params=params)
        return resp.json()["data"]
    
    def get(self, agent_id):
        resp = self._client._request("GET", f"/api/v1/agents/{agent_id}")
        return resp.json()["data"]