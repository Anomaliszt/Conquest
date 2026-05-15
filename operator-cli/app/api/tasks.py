class TasksClient:
    def __init__(self, client):
        self._client = client
    
    def list(self, agent_id=None, status=None):
        params = {}
        if agent_id:
            params["agent_id"] = agent_id
        if status:
            params["status"] = status
        resp = self._client._request("GET", "/api/v1/tasks", params=params)
        return resp.json()["data"]
    
    def get(self, task_id):
        resp = self._client._request("GET", f"/api/v1/tasks/{task_id}")
        return resp.json()["data"]
    
    def result(self, task_id):
        resp = self._client._request("GET", f"/api/v1/tasks/{task_id}/result")
        return resp.json()["data"]
    
    def cancel(self, task_id):
        resp = self._client._request("POST", f"/api/v1/tasks/{task_id}/cancel")
        return resp.json()["data"]
    
    def create(self, agent_id, command, payload=None):
        data = {"type": command, "payload": payload or {}}
        resp = self._client._request(
            "POST",
            f"/api/v1/agents/{agent_id}/tasks",
            json=data
        )
        return resp.json()["data"]