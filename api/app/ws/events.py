from typing import Dict, Any

from api.app.repositories.operator_events_repo import create_operator_event
from api.app.ws.manager import manager
from api.app.ws.messages import build_operator_event


def emit_operator_event(socketio, event_type: str, data: Dict[str, Any]):
    event = create_operator_event(event_type, data)

    message = build_operator_event(
        event_id=event.id,
        cursor=event.cursor,
        event_type=event.event_type,
        created_at=event.created_at,
        data=event.data,
    )

    socketio.emit("operator_event", message, namespace="/ws/operator/events")


def emit_agent_task(socketio, agent_id: str, message: dict):
    sid = manager.get_agent_sid(agent_id)
    if sid:
        socketio.emit("message", message, to=sid, namespace="/ws/agent/tasks")