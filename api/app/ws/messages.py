from enum import Enum
from typing import Optional, Any, Literal
from pydantic import BaseModel, Field


class MessageType(str, Enum):
    TASK_DISPATCHED = "task_dispatched"
    TASK_CANCEL_REQUESTED = "task_cancel_requested"
    TASK_ACK = "task_ack"
    TASK_RESULT = "task_result"
    TASK_CANCELLED = "task_cancelled"
    AGENT_WS_ERROR = "agent_ws_error"
    OPERATOR_EVENT = "operator_event"


class TaskCommand(str, Enum):
    WHOAMI = "whoami"
    UPTIME = "uptime"
    SHELL_EXECUTE = "shell_execute"


class TaskStatus(str, Enum):
    QUEUED = "queued"
    DISPATCHED = "dispatched"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLATION_REQUESTED = "cancellation_requested"
    CANCELLED = "cancelled"
    ORPHANED = "orphaned"


class AgentWsErrorCode(str, Enum):
    BAD_MESSAGE = "BAD_MESSAGE"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    CONFLICT = "CONFLICT"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class OperatorEventType(str, Enum):
    AGENT_REGISTERED = "agent_registered"
    AGENT_TOKEN_REFRESHED = "agent_token_refreshed"
    AGENT_REFRESH_TOKEN_REVOKED = "agent_refresh_token_revoked"
    AGENT_HEARTBEAT = "agent_heartbeat"
    AGENT_DECOMMISSIONED = "agent_decommissioned"
    TASK_CREATED = "task_created"
    TASK_DISPATCHED = "task_dispatched"
    TASK_RUNNING = "task_running"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCEL_REQUESTED = "task_cancel_requested"
    TASK_CANCELLED = "task_cancelled"
    TASK_ORPHANED = "task_orphaned"


class TaskDispatchedPayload(BaseModel):
    type: Literal["task_dispatched"] = "task_dispatched"
    task_id: str = Field(pattern=r"^task_[A-Za-z0-9_-]{3,64}$")
    task_type: TaskCommand
    payload: dict = Field(default_factory=dict)
    dispatched_at: str
    ack_deadline_at: str
    run_deadline_at: str


class TaskCancelRequestedPayload(BaseModel):
    type: Literal["task_cancel_requested"] = "task_cancel_requested"
    task_id: str = Field(pattern=r"^task_[A-Za-z0-9_-]{3,64}$")
    requested_at: str
    cancel_deadline_at: str
    reason: Optional[str] = None


class TaskAckPayload(BaseModel):
    type: Literal["task_ack"] = "task_ack"
    task_id: str = Field(pattern=r"^task_[A-Za-z0-9_-]{3,64}$")
    status: Literal["running"] = "running"
    acknowledged_at: str


class TaskResultPayload(BaseModel):
    type: Literal["task_result"] = "task_result"
    task_id: str = Field(pattern=r"^task_[A-Za-z0-9_-]{3,64}$")
    status: Literal["completed", "failed"]
    exit_code: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    completed_at: str


class TaskCancelledPayload(BaseModel):
    type: Literal["task_cancelled"] = "task_cancelled"
    task_id: str = Field(pattern=r"^task_[A-Za-z0-9_-]{3,64}$")
    status: Literal["cancelled"] = "cancelled"
    partial: bool
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    cancelled_at: str


class AgentWsErrorPayload(BaseModel):
    type: Literal["agent_ws_error"] = "agent_ws_error"
    code: AgentWsErrorCode
    message: str
    task_id: Optional[str] = None


class OperatorEventPayload(BaseModel):
    type: Literal["operator_event"] = "operator_event"
    id: str
    cursor: str
    event_type: OperatorEventType
    created_at: str
    data: dict


def parse_agent_message(data: dict) -> tuple[MessageType, BaseModel]:
    msg_type = data.get("type")
    if not msg_type:
        raise ValueError("Missing required field: type")

    msg_enum = MessageType(msg_type)

    parsers = {
        MessageType.TASK_ACK: TaskAckPayload,
        MessageType.TASK_RESULT: TaskResultPayload,
        MessageType.TASK_CANCELLED: TaskCancelledPayload,
    }

    parser = parsers.get(msg_enum)
    if not parser:
        raise ValueError(f"Unknown or unsupported agent message type: {msg_type}")

    return msg_enum, parser(**data)


def build_task_dispatched(
    task_id: str,
    task_type: str,
    payload: dict,
    dispatched_at: str,
    ack_deadline_at: str,
    run_deadline_at: str,
) -> dict:
    return TaskDispatchedPayload(
        task_id=task_id,
        task_type=TaskCommand(task_type),
        payload=payload,
        dispatched_at=dispatched_at,
        ack_deadline_at=ack_deadline_at,
        run_deadline_at=run_deadline_at,
    ).model_dump()


def build_task_cancel_requested(
    task_id: str,
    requested_at: str,
    cancel_deadline_at: str,
    reason: Optional[str] = None,
) -> dict:
    return TaskCancelRequestedPayload(
        task_id=task_id,
        requested_at=requested_at,
        cancel_deadline_at=cancel_deadline_at,
        reason=reason,
    ).model_dump()


def build_agent_ws_error(
    code: AgentWsErrorCode,
    message: str,
    task_id: Optional[str] = None,
) -> dict:
    return AgentWsErrorPayload(
        code=code,
        message=message,
        task_id=task_id,
    ).model_dump()


def build_operator_event(
    event_id: str,
    cursor: str,
    event_type: str,
    created_at: str,
    data: dict,
) -> dict:
    return OperatorEventPayload(
        id=event_id,
        cursor=cursor,
        event_type=OperatorEventType(event_type),
        created_at=created_at,
        data=data,
    ).model_dump()