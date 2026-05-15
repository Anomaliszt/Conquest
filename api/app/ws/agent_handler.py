from datetime import datetime, timezone, timedelta
from flask import request
from flask_socketio import emit, disconnect

from api.app.core.jwt import verify_agent_token
from api.app.repositories.tasks_repo import get_task_by_id, update_task_status, list_tasks
from api.app.utils.time import now_iso
from api.app.ws.events import emit_operator_event
from api.app.ws.manager import manager
from api.app.ws.messages import (
    parse_agent_message,
    MessageType,
    build_agent_ws_error,
    AgentWsErrorCode,
    build_task_dispatched,
    build_task_cancel_requested,
)


def require_agent_auth(token: str):
    payload = verify_agent_token(token)
    if not payload:
        return None, "Invalid or expired token"
    if payload.get("scope") != "agent":
        return None, "Invalid token scope"
    agent_id = payload.get("sub")
    if not agent_id:
        return None, "Missing agent identity"
    return agent_id, None


def _is_deadline_exceeded(deadline_at: str) -> bool:
    """Check if a deadline has been exceeded. Returns True if exceeded."""
    try:
        deadline = datetime.fromisoformat(deadline_at.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        return now > deadline
    except (ValueError, AttributeError):
        return False


def handle_connect(socketio):
    token = request.args.get("token")
    if not token:
        emit("message", build_agent_ws_error(
            AgentWsErrorCode.UNAUTHORIZED,
            "Missing authentication token"
        ))
        disconnect(code=4001)
        return None

    agent_id, error = require_agent_auth(token)
    if error:
        emit("message", build_agent_ws_error(
            AgentWsErrorCode.UNAUTHORIZED,
            error
        ))
        disconnect(code=4001)
        return None

    old_sid = manager.register_agent(request.sid, agent_id)
    if old_sid:
        # Duplicate connection detected - reject the new connection with error
        emit("message", build_agent_ws_error(
            AgentWsErrorCode.CONFLICT,
            "Duplicate connection for this agent",
            task_id="system"
        ))
        disconnect(code=4409)
        return None

    _replay_unacknowledged_tasks(socketio, agent_id)

    return agent_id


def handle_disconnect():
    return manager.unregister_agent(request.sid)


def handle_message(socketio, data):
    agent_id = manager.get_agent_id(request.sid)
    if not agent_id:
        emit("message", build_agent_ws_error(
            AgentWsErrorCode.UNAUTHORIZED,
            "Not authenticated"
        ))
        return

    try:
        msg_type, payload = parse_agent_message(data)
    except ValueError as e:
        emit("message", build_agent_ws_error(
            AgentWsErrorCode.BAD_MESSAGE,
            str(e)
        ))
        return

    handlers = {
        MessageType.TASK_ACK: _handle_task_ack,
        MessageType.TASK_RESULT: _handle_task_result,
        MessageType.TASK_CANCELLED: _handle_task_cancelled,
    }

    handler = handlers.get(msg_type)
    if handler:
        handler(socketio, agent_id, payload)


def _handle_task_ack(socketio, agent_id: str, payload):
    task_id = payload.task_id
    
    # Check idempotency - ignore duplicate acks
    if not manager.mark_task_processed(agent_id, f"ack:{task_id}"):
        # Duplicate ack, ignore silently per contract
        return
    
    task = get_task_by_id(task_id)

    if not task:
        emit("message", build_agent_ws_error(
            AgentWsErrorCode.CONFLICT,
            "Task not found",
            task_id
        ))
        return

    if task.agent_id != agent_id:
        emit("message", build_agent_ws_error(
            AgentWsErrorCode.FORBIDDEN,
            "Task does not belong to this agent",
            task_id
        ))
        return

    if task.status != "dispatched":
        emit("message", build_agent_ws_error(
            AgentWsErrorCode.CONFLICT,
            "Invalid task state transition",
            task_id
        ))
        return

    # Check ack deadline
    if task.ack_deadline_at and _is_deadline_exceeded(task.ack_deadline_at):
        emit("message", build_agent_ws_error(
            AgentWsErrorCode.CONFLICT,
            "Ack deadline exceeded",
            task_id
        ))
        update_task_status(task_id, "failed", now_iso(), failure_reason="Ack deadline exceeded")
        emit_operator_event(socketio, "task_failed", {
            "task_id": task_id,
            "agent_id": agent_id,
            "status": "failed",
            "reason": "Ack deadline exceeded",
        })
        return

    update_task_status(task_id, "running", now_iso(), started_at=now_iso())

    emit_operator_event(socketio, "task_running", {
        "task_id": task_id,
        "agent_id": agent_id,
        "status": "running",
    })


def _handle_task_result(socketio, agent_id: str, payload):
    task_id = payload.task_id
    
    # Check idempotency - ignore duplicate results
    if not manager.mark_task_processed(agent_id, f"result:{task_id}"):
        # Duplicate result, ignore silently per contract
        return
    
    task = get_task_by_id(task_id)

    if not task:
        emit("message", build_agent_ws_error(
            AgentWsErrorCode.CONFLICT,
            "Task not found",
            task_id
        ))
        return

    if task.agent_id != agent_id:
        emit("message", build_agent_ws_error(
            AgentWsErrorCode.FORBIDDEN,
            "Task does not belong to this agent",
            task_id
        ))
        return

    if task.status not in ["dispatched", "running"]:
        emit("message", build_agent_ws_error(
            AgentWsErrorCode.CONFLICT,
            "Invalid task state transition",
            task_id
        ))
        return

    # Check run deadline
    if task.run_deadline_at and _is_deadline_exceeded(task.run_deadline_at):
        emit("message", build_agent_ws_error(
            AgentWsErrorCode.CONFLICT,
            "Run deadline exceeded",
            task_id
        ))
        # Still record the result but mark it as failed due to deadline
        result_data = {
            "status": "failed",
            "exit_code": payload.exit_code,
            "result_stdout": payload.stdout,
            "result_stderr": payload.stderr,
            "failure_reason": "Run deadline exceeded",
        }
        update_task_status(task_id, "failed", now_iso(), **result_data)
        emit_operator_event(socketio, "task_failed", {
            "task_id": task_id,
            "agent_id": agent_id,
            "status": "failed",
            "reason": "Run deadline exceeded",
            "result_available": True,
        })
        return

    status = payload.status
    result_data = {
        "status": status,
        "exit_code": payload.exit_code,
        "result_stdout": payload.stdout,
        "result_stderr": payload.stderr,
    }

    if status == "failed":
        result_data["failure_reason"] = payload.stderr or "Task failed"

    update_task_status(task_id, status, now_iso(), **result_data)

    event_type = "task_completed" if status == "completed" else "task_failed"
    emit_operator_event(socketio, event_type, {
        "task_id": task_id,
        "agent_id": agent_id,
        "status": status,
        "result_available": True,
    })


def _handle_task_cancelled(socketio, agent_id: str, payload):
    task_id = payload.task_id
    
    # Check idempotency - ignore duplicate cancellations
    if not manager.mark_task_processed(agent_id, f"cancelled:{task_id}"):
        # Duplicate cancellation, ignore silently per contract
        return
    
    task = get_task_by_id(task_id)

    if not task:
        emit("message", build_agent_ws_error(
            AgentWsErrorCode.CONFLICT,
            "Task not found",
            task_id
        ))
        return

    if task.agent_id != agent_id:
        emit("message", build_agent_ws_error(
            AgentWsErrorCode.FORBIDDEN,
            "Task does not belong to this agent",
            task_id
        ))
        return

    if task.status not in ["dispatched", "running", "cancellation_requested"]:
        emit("message", build_agent_ws_error(
            AgentWsErrorCode.CONFLICT,
            "Invalid task state transition",
            task_id
        ))
        return

    # Check cancel deadline if applicable
    cancel_deadline_exceeded = False
    if task.cancel_requested_at:
        # Estimate cancel_deadline_at as cancel_requested_at + 10 seconds (default timeout)
        # In production, this should be stored in DB
        try:
            cancel_req_time = datetime.fromisoformat(task.cancel_requested_at.replace('Z', '+00:00'))
            cancel_deadline = cancel_req_time.replace(microsecond=0)
            cancel_deadline = cancel_deadline.replace(second=cancel_deadline.second + 10)
            now = datetime.now(timezone.utc)
            cancel_deadline_exceeded = now > cancel_deadline
        except (ValueError, AttributeError):
            pass

    if cancel_deadline_exceeded:
        emit("message", build_agent_ws_error(
            AgentWsErrorCode.CONFLICT,
            "Cancel deadline exceeded",
            task_id
        ))

    update_task_status(
        task_id,
        "cancelled",
        now_iso(),
        result_stdout=payload.stdout,
        result_stderr=payload.stderr,
    )

    emit_operator_event(socketio, "task_cancelled", {
        "task_id": task_id,
        "agent_id": agent_id,
        "status": "cancelled",
        "partial_output_available": payload.partial,
    })


def _replay_unacknowledged_tasks(socketio, agent_id: str):
    tasks, _ = list_tasks(agent_id=agent_id, status="dispatched", limit=100)

    for task in tasks:
        message = build_task_dispatched(
            task_id=task.id,
            task_type=task.type,
            payload=task.payload or {},
            dispatched_at=task.dispatched_at,
            ack_deadline_at=task.ack_deadline_at,
            run_deadline_at=task.run_deadline_at,
        )
        emit("message", message)


def send_task_cancel_request(socketio, task_id: str, agent_id: str, reason: str = None):
    """Send a task cancellation request to an agent via WebSocket.
    
    This is called from the tasks service when an operator or system requests cancellation.
    """
    task = get_task_by_id(task_id)
    if not task:
        return False, "Task not found"
    
    if task.agent_id != agent_id:
        return False, "Task does not belong to this agent"
    
    if task.status not in ["dispatched", "running"]:
        return False, f"Cannot cancel task in {task.status} status"
    
    # Update task status to cancellation_requested
    cancel_requested_at = now_iso()
    update_task_status(task_id, "cancellation_requested", cancel_requested_at, cancel_requested_at=cancel_requested_at)
    
    # Calculate cancel deadline (10 seconds from now)
    now = datetime.now(timezone.utc)
    cancel_deadline = now.replace(microsecond=0) + timedelta(seconds=10)
    cancel_deadline_at = cancel_deadline.isoformat().replace('+00:00', 'Z')
    
    # Send cancel request message to agent
    message = build_task_cancel_requested(
        task_id=task_id,
        requested_at=cancel_requested_at,
        cancel_deadline_at=cancel_deadline_at,
        reason=reason,
    )
    
    sid = manager.get_agent_sid(agent_id)
    if sid:
        socketio.emit("message", message, to=sid, namespace="/ws/agent/tasks")
    else:
        return False, "Agent not currently connected"
    
    # Emit operator event
    emit_operator_event(socketio, "task_cancel_requested", {
        "task_id": task_id,
        "agent_id": agent_id,
        "reason": reason or "Cancellation requested",
    })
    
    return True, "Cancel request sent"