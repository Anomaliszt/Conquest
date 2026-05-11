import uuid
from enum import Enum
from api.app.utils.time import now_iso
from api.app.repositories.tasks_repo import (
    create_task,
    get_task_by_id,
    list_tasks,
    update_task_status,
    get_task_result,
)
from api.app.repositories.agents_repo import get_agent_by_id


class TaskCommand(str, Enum):
    WHOAMI = "whoami"
    UPTIME = "uptime"
    SHELL_EXECUTE = "shell_execute"

    def accepts_payload(self) -> bool:
        return self is TaskCommand.SHELL_EXECUTE


TERMINAL_STATUSES = ["completed", "failed", "cancelled", "orphaned"]


def generate_task_id():
    return f"task_{uuid.uuid4().hex[:12]}"


def create_task_for_agent(agent_id, task_type, payload, max_attempts=3, run_timeout_seconds=3600):
    try:
        command = TaskCommand(task_type)
    except ValueError:
        return None, (f"unsupported task type: {task_type}", 422)

    agent = get_agent_by_id(agent_id)
    if not agent:
        return None, ("agent not found", 404)

    if agent.status not in ["online", "offline"]:
        return None, ("agent not available for tasks", 400)

    if command.accepts_payload():
        if not isinstance(payload, dict) or "command" not in payload:
            return None, ("shell_execute requires 'command' in payload", 400)
    else:
        if payload:
            return None, (f"{task_type} does not accept payload", 400)

    task_id = generate_task_id()
    created_at = now_iso()

    task = create_task(
        task_id=task_id,
        agent_id=agent_id,
        task_type=command.value,
        payload=payload,
        status="queued",
        attempt_count=0,
        max_attempts=max_attempts,
        run_timeout_seconds=run_timeout_seconds,
        created_at=created_at,
        updated_at=created_at,
    )

    return task, None


def get_task(task_id):
    return get_task_by_id(task_id)


def list_all_tasks(status=None, agent_id=None, limit=50, offset=0):
    return list_tasks(status=status, agent_id=agent_id, limit=limit, offset=offset)


def cancel_task(task_id, reason=None, grace_period_seconds=30):
    task = get_task_by_id(task_id)
    if not task:
        return None, ("task not found", 404)

    if task.status in TERMINAL_STATUSES:
        return None, (f"cannot cancel task in {task.status} status", 409)

    updated_at = now_iso()

    if task.status == "queued":
        return update_task_status(
            task_id, "cancelled", updated_at, cancel_requested_at=updated_at
        ), None

    return update_task_status(
        task_id,
        "cancellation_requested",
        updated_at,
        cancel_requested_at=updated_at,
    ), None


def get_result(task_id):
    task = get_task_result(task_id)
    if not task:
        return None, ("task not found", 404)

    if task.status not in TERMINAL_STATUSES:
        return None, ("task result not available yet", 404)

    return {
        "task_id": task.id,
        "exit_code": task.exit_code,
        "stdout": task.result_stdout,
        "stderr": task.result_stderr,
        "failure_reason": task.failure_reason,
    }, None


def update_status(task_id, new_status, **kwargs):
    task = get_task_by_id(task_id)
    if not task:
        return None, ("task not found", 404)

    allowed = TERMINAL_STATUSES + ["dispatched", "running"]
    if new_status not in allowed:
        return None, (f"invalid status: {new_status}", 400)

    updated_at = now_iso()
    return update_task_status(task_id, new_status, updated_at, **kwargs), None