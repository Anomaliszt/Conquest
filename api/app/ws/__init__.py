from typing import Any

from flask_socketio import SocketIO

from api.app.ws import agent_handler, operator_handler
from api.app.ws.manager import manager
from api.app.ws.messages import build_task_dispatched, build_task_cancel_requested

socketio = SocketIO(cors_allowed_origins="*")


def init_socketio(app):
    socketio.init_app(app, async_mode="eventlet")


def register_handlers():
    @socketio.on("connect", namespace="/ws/agent/tasks")
    def handle_agent_connect():
        return agent_handler.handle_connect(socketio)

    @socketio.on("disconnect", namespace="/ws/agent/tasks")
    def handle_agent_disconnect():
        return agent_handler.handle_disconnect()

    @socketio.on("message", namespace="/ws/agent/tasks")
    def handle_agent_message(data):
        return agent_handler.handle_message(socketio, data)

    @socketio.on("connect", namespace="/ws/operator/events")
    def handle_operator_connect():
        return operator_handler.handle_connect(socketio)

    @socketio.on("disconnect", namespace="/ws/operator/events")
    def handle_operator_disconnect():
        return operator_handler.handle_disconnect()


def emit_task_dispatched(agent_id: str, task: Any):
    """Emit a task_dispatched message to a specific agent."""
    message = build_task_dispatched(
        task_id=task.id,
        task_type=task.type,
        payload=task.payload or {},
        dispatched_at=task.dispatched_at,
        ack_deadline_at=task.ack_deadline_at,
        run_deadline_at=task.run_deadline_at,
    )
    
    sid = manager.get_agent_sid(agent_id)
    if sid:
        socketio.emit("message", message, to=sid, namespace="/ws/agent/tasks")


def emit_task_cancel_requested(agent_id: str, task_id: str, requested_at: str, cancel_deadline_at: str, reason: str = None):
    """Emit a task_cancel_requested message to a specific agent."""
    return agent_handler.send_task_cancel_request(socketio, task_id, agent_id, reason)