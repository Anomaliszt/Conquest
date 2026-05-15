from typing import Optional, Dict, Set


class WebSocketManager:
    def __init__(self):
        self._agent_connections: Dict[str, str] = {}
        self._operator_connections: Dict[str, Set[str]] = {}
        self._sid_to_agent: Dict[str, str] = {}
        self._sid_to_operator: Dict[str, str] = {}
        self._agent_processed_tasks: Dict[str, Set[str]] = {}  # agent_id -> set of processed task_ids for idempotency

    def register_agent(self, sid: str, agent_id: str) -> Optional[str]:
        """Register an agent connection. Returns old_sid if duplicate connection detected."""
        if agent_id in self._agent_connections:
            old_sid = self._agent_connections[agent_id]
            if old_sid != sid:
                return old_sid
        self._agent_connections[agent_id] = sid
        self._sid_to_agent[sid] = agent_id
        if agent_id not in self._agent_processed_tasks:
            self._agent_processed_tasks[agent_id] = set()
        return None

    def unregister_agent(self, sid: str) -> Optional[str]:
        agent_id = self._sid_to_agent.pop(sid, None)
        if agent_id:
            if self._agent_connections.get(agent_id) == sid:
                self._agent_connections.pop(agent_id, None)
                self.clear_processed_tasks(agent_id)
        return agent_id

    def get_agent_sid(self, agent_id: str) -> Optional[str]:
        return self._agent_connections.get(agent_id)

    def get_agent_id(self, sid: str) -> Optional[str]:
        return self._sid_to_agent.get(sid)

    def register_operator(self, sid: str, operator_id: str):
        if operator_id not in self._operator_connections:
            self._operator_connections[operator_id] = set()
        self._operator_connections[operator_id].add(sid)
        self._sid_to_operator[sid] = operator_id

    def unregister_operator(self, sid: str) -> Optional[str]:
        operator_id = self._sid_to_operator.pop(sid, None)
        if operator_id and operator_id in self._operator_connections:
            self._operator_connections[operator_id].discard(sid)
            if not self._operator_connections[operator_id]:
                self._operator_connections.pop(operator_id, None)
        return operator_id

    def get_operator_sids(self, operator_id: str) -> Set[str]:
        return self._operator_connections.get(operator_id, set())

    def get_all_operator_sids(self) -> Set[str]:
        return set(self._sid_to_operator.keys())

    def is_agent_connected(self, agent_id: str) -> bool:
        return agent_id in self._agent_connections

    def mark_task_processed(self, agent_id: str, task_id: str) -> bool:
        """Mark a task as processed by an agent. Returns True if first time, False if duplicate."""
        if agent_id not in self._agent_processed_tasks:
            self._agent_processed_tasks[agent_id] = set()
        if task_id in self._agent_processed_tasks[agent_id]:
            return False  # Already processed
        self._agent_processed_tasks[agent_id].add(task_id)
        return True  # First time processing

    def clear_processed_tasks(self, agent_id: str):
        """Clear processed tasks when agent disconnects."""
        self._agent_processed_tasks.pop(agent_id, None)


manager = WebSocketManager()