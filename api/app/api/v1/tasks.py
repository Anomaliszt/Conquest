from flask import Blueprint, request

from api.app.schemas.errors import APIError
from api.app.dependencies import require_operator_auth
from api.app.schemas import (
    CreateTaskRequest,
    TaskResponse,
    TaskListResponse,
    CancelTaskRequest,
    CancelTaskResponse,
    TaskResultResponse,
    SendAllTasksRequest,
    SendAllTasksResponse,
    TaskHistoryListResponse,
)
from api.app.services.tasks_service import (
    create_task_for_agent,
    get_task,
    list_all_tasks,
    cancel_task,
    get_result,
)
from api.app.repositories.agents_repo import list_agents
from api.app.ws import socketio
from api.app.ws.events import emit_operator_event
from api.app.repositories.tasks_repo import update_task_status
from api.app.utils.time import now_iso

tasks_bp = Blueprint("tasks", __name__)


@tasks_bp.post("/api/v1/agents/<agent_id>/tasks")
@require_operator_auth
def create_task_route(agent_id, operator_id):
    data = CreateTaskRequest(**request.get_json())

    task, error = create_task_for_agent(
        agent_id=agent_id,
        task_type=data.type,
        payload=data.payload,
        max_attempts=data.max_attempts,
        run_timeout_seconds=data.run_timeout_seconds,
    )

    if error:
        message, status_code = error
        raise APIError(
            code={404: "NOT_FOUND", 400: "BAD_REQUEST", 422: "UNPROCESSABLE_ENTITY"}.get(
                status_code, "INTERNAL_ERROR"
            ),
            message=message,
            status=status_code,
        )

    emit_operator_event(socketio, "task_created", {
        "task_id": task.id,
        "agent_id": agent_id,
        "task_type": task.type,
        "status": task.status,
    })

    return {"data": _task_to_dict(task)}, 201


@tasks_bp.get("/api/v1/tasks")
@require_operator_auth
def list_tasks_route(operator_id):
    status = request.args.get("status")
    agent_id = request.args.get("agent_id")
    sort = request.args.get("sort", "created_at_desc")

    try:
        page_size = int(request.args.get("page_size", 50))
        page_size = min(max(page_size, 1), 1000)
    except (ValueError, TypeError):
        raise APIError(code="BAD_REQUEST", message="Invalid page_size", status=400)

    try:
        cursor = int(request.args.get("cursor", 0))
        cursor = max(cursor, 0)
    except (ValueError, TypeError):
        cursor = 0

    tasks, total = list_all_tasks(
        status=status,
        agent_id=agent_id,
        limit=page_size,
        offset=cursor,
    )

    has_more = cursor + len(tasks) < total
    next_cursor = str(cursor + len(tasks)) if has_more else None

    return TaskListResponse(
        data=[_task_to_dict(t) for t in tasks],
        pagination={
            "page_size": page_size,
            "next_cursor": next_cursor,
            "has_more": has_more,
            "sort": sort,
        },
    ).model_dump(), 200


@tasks_bp.get("/api/v1/tasks/<task_id>")
@require_operator_auth
def get_task_route(task_id, operator_id):
    task = get_task(task_id)
    if not task:
        raise APIError(code="NOT_FOUND", message="task not found", status=404)

    return TaskResponse(data=_task_to_dict(task)).model_dump(), 200


@tasks_bp.post("/api/v1/tasks/<task_id>/cancel")
@require_operator_auth
def cancel_task_route(task_id, operator_id):
    data = CancelTaskRequest(**request.get_json()) if request.get_json() else CancelTaskRequest()

    result, error = cancel_task(
        task_id=task_id,
        reason=data.reason,
        grace_period_seconds=data.grace_period_seconds,
    )

    if error:
        message, status_code = error
        raise APIError(
            code={404: "NOT_FOUND", 409: "CONFLICT"}.get(status_code, "INTERNAL_ERROR"),
            message=message,
            status=status_code,
        )

    if result.status == "cancellation_requested":
        from datetime import datetime, timedelta, timezone
        from api.app.ws import emit_task_cancel_requested

        now = datetime.now(timezone.utc)
        cancel_deadline = now + timedelta(seconds=data.grace_period_seconds or 30)

        emit_task_cancel_requested(
            task_id=result.id,
            agent_id=result.agent_id,
            requested_at=now.isoformat().replace('+00:00', 'Z'),
            cancel_deadline_at=cancel_deadline.isoformat().replace('+00:00', 'Z'),
            reason=data.reason,
        )

    emit_operator_event(socketio, "task_cancel_requested", {
        "task_id": result.id,
        "agent_id": result.agent_id,
        "reason": data.reason,
    })

    return CancelTaskResponse(
        task_id=result.id,
        status=result.status,
        message="cancellation requested" if result.status == "cancellation_requested" else "task cancelled",
    ).model_dump(), 200


@tasks_bp.get("/api/v1/tasks/<task_id>/result")
@require_operator_auth
def get_result_route(task_id, operator_id):
    result, error = get_result(task_id)

    if error:
        message, status_code = error
        raise APIError(
            code={404: "NOT_FOUND"}.get(status_code, "INTERNAL_ERROR"),
            message=message,
            status=status_code,
        )

    return TaskResultResponse(data=result).model_dump(), 200


@tasks_bp.post("/api/v1/tasks/send-all")
@require_operator_auth
def send_all_tasks_route(operator_id):
    data = SendAllTasksRequest(**request.get_json())

    if data.dry_run:
        agents, _ = list_agents(status="online")
        agent_ids = [a.id for a in agents]
        return SendAllTasksResponse(task_ids=agent_ids, count=len(agent_ids)).model_dump(), 200

    agents, _ = list_agents(status="online")
    agent_ids = [a.id for a in agents]

    if data.filter:
        if "status" in data.filter:
            filtered_agents, _ = list_agents(status=data.filter["status"])
            agent_ids = [a.id for a in filtered_agents]

    task_ids = []
    for agent_id in agent_ids:
        task, error = create_task_for_agent(
            agent_id=agent_id,
            task_type=data.type,
            payload=data.payload,
            max_attempts=data.max_attempts,
            run_timeout_seconds=data.run_timeout_seconds,
        )
        if task:
            task_ids.append(task.id)

    return SendAllTasksResponse(task_ids=task_ids, count=len(task_ids)).model_dump(), 202


@tasks_bp.get("/api/v1/task-history")
@require_operator_auth
def task_history_route(operator_id):
    sort = request.args.get("sort", "created_at_desc")

    try:
        page_size = int(request.args.get("page_size", 50))
        page_size = min(max(page_size, 1), 1000)
    except (ValueError, TypeError):
        raise APIError(code="BAD_REQUEST", message="Invalid page_size", status=400)

    try:
        cursor = int(request.args.get("cursor", 0))
        cursor = max(cursor, 0)
    except (ValueError, TypeError):
        cursor = 0

    tasks, total = list_all_tasks(limit=page_size, offset=cursor)

    has_more = cursor + len(tasks) < total
    next_cursor = str(cursor + len(tasks)) if has_more else None

    return TaskHistoryListResponse(
        data=[_task_history_entry(t) for t in tasks],
        pagination={
            "page_size": page_size,
            "next_cursor": next_cursor,
            "has_more": has_more,
            "sort": sort,
        },
    ).model_dump(), 200


def _task_to_dict(task):
    return {
        "id": task.id,
        "agent_id": task.agent_id,
        "type": task.type,
        "payload": task.payload,
        "status": task.status,
        "attempt_count": task.attempt_count,
        "max_attempts": task.max_attempts,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "dispatched_at": task.dispatched_at,
        "ack_deadline_at": task.ack_deadline_at,
        "run_deadline_at": task.run_deadline_at,
        "started_at": task.started_at,
        "completed_at": task.completed_at,
        "cancel_requested_at": task.cancel_requested_at,
        "exit_code": task.exit_code,
        "failure_reason": task.failure_reason,
    }


def _task_history_entry(task):
    return {
        "task_id": task.id,
        "agent_id": task.agent_id,
        "type": task.type,
        "payload": task.payload,
        "status": task.status,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "dispatched_at": task.dispatched_at,
        "started_at": task.started_at,
        "completed_at": task.completed_at,
        "cancel_requested_at": task.cancel_requested_at,
        "attempt_count": task.attempt_count,
        "exit_code": task.exit_code,
        "failure_reason": task.failure_reason,
        "result_available": task.status in ["completed", "failed"] and task.result_stdout is not None,
    }