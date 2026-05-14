"""Pydantic schemas for task endpoints."""

from pydantic import BaseModel, Field
from typing import Literal, Optional


class CreateTaskRequest(BaseModel):
    type: Literal["whoami", "uptime", "shell_execute"] = Field(
        ..., description="Task command type"
    )
    payload: dict = Field(default_factory=dict, description="Command payload")
    max_attempts: int = Field(default=3, ge=1, le=5, description="Max retry attempts")
    run_timeout_seconds: int = Field(default=3600, ge=1, le=86400, description="Timeout")


class Task(BaseModel):
    id: str
    agent_id: str
    type: str
    payload: dict
    status: str
    attempt_count: int
    max_attempts: int
    created_at: str
    updated_at: str
    dispatched_at: Optional[str] = None
    ack_deadline_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    cancel_requested_at: Optional[str] = None
    exit_code: Optional[int] = None
    failure_reason: Optional[str] = None


class TaskResponse(BaseModel):
    data: Task


class TaskListResponse(BaseModel):
    data: list[Task]
    pagination: dict


class CancelTaskRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=1000, description="Cancellation reason")
    grace_period_seconds: int = Field(default=30, ge=1, description="Grace period")


class CancelTaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskResult(BaseModel):
    task_id: str
    exit_code: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    failure_reason: Optional[str] = None


class TaskResultResponse(BaseModel):
    data: TaskResult


class SendAllTasksRequest(BaseModel):
    type: Literal["whoami", "uptime", "shell_execute"] = Field(
        ..., description="Task command type"
    )
    payload: dict = Field(default_factory=dict, description="Command payload")
    filter: Optional[dict] = Field(default=None, description="Agent filter criteria")
    dry_run: bool = Field(default=False, description="Preview without creating tasks")
    max_attempts: int = Field(default=3, ge=1, le=5, description="Max retry attempts")
    run_timeout_seconds: int = Field(default=3600, ge=1, le=86400, description="Timeout")


class SendAllTasksResponse(BaseModel):
    task_ids: list[str]
    count: int


class TaskHistoryEntry(BaseModel):
    task_id: str
    agent_id: str
    type: str
    payload: dict
    status: str
    created_at: str
    updated_at: str
    dispatched_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    cancel_requested_at: Optional[str] = None
    attempt_count: int
    exit_code: Optional[int] = None
    failure_reason: Optional[str] = None
    result_available: bool


class TaskHistoryListResponse(BaseModel):
    data: list[TaskHistoryEntry]
    pagination: dict