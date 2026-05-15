from datetime import datetime, timezone

from flask import request
from flask_socketio import emit, disconnect

from api.app.core.jwt import verify_operator_token
from api.app.repositories.operator_events_repo import get_events_after_cursor, get_recent_events
from api.app.ws.manager import manager
from api.app.ws.messages import build_operator_event


OPERATOR_EVENT_RETENTION_SECONDS = 86400


def require_operator_auth(token: str):
    payload = verify_operator_token(token)
    if not payload:
        return None, "Invalid or expired token"
    if payload.get("scope") != "operator":
        return None, "Invalid token scope"
    operator_id = payload.get("sub")
    if not operator_id:
        return None, "Missing operator identity"
    return operator_id, None


def handle_connect(socketio):
    token = request.args.get("token")
    if not token:
        emit("operator_event", {"error": "Missing authentication token"})
        disconnect(code=4001)
        return None

    operator_id, error = require_operator_auth(token)
    if error:
        emit("operator_event", {"error": error})
        disconnect(code=4001)
        return None

    manager.register_operator(request.sid, operator_id)

    cursor = request.args.get("cursor")
    if cursor:
        events, error = _get_events_with_cursor_validation(cursor)
        if error:
            emit("operator_event", {
                "error": error["message"],
                "code": error["code"],
            })
            disconnect(code=4404)
            return None
        for event in events:
            emit("operator_event", build_operator_event(
                event_id=event.id,
                cursor=event.cursor,
                event_type=event.event_type,
                created_at=event.created_at,
                data=event.data,
            ))
    else:
        recent_events = get_recent_events(limit=50)
        for event in recent_events:
            emit("operator_event", build_operator_event(
                event_id=event.id,
                cursor=event.cursor,
                event_type=event.event_type,
                created_at=event.created_at,
                data=event.data,
            ))

    return operator_id


def handle_disconnect():
    return manager.unregister_operator(request.sid)


def _get_events_with_cursor_validation(cursor: str):
    try:
        events = get_events_after_cursor(cursor, limit=100)
    except Exception:
        return None, {"code": "cursor_expired", "message": "Cursor expired or invalid"}

    if not events:
        return [], None

    first_event = events[0]
    try:
        event_time = datetime.fromisoformat(first_event.created_at.replace('Z', '+00:00'))
    except ValueError:
        return None, {"code": "cursor_expired", "message": "Invalid cursor format"}

    now = datetime.now(timezone.utc)
    age = (now - event_time).total_seconds()

    if age > OPERATOR_EVENT_RETENTION_SECONDS:
        return None, {"code": "cursor_expired", "message": "Cursor expired"}

    return events, None