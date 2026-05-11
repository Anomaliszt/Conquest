from sqlalchemy import Column, String, JSON, Integer, ForeignKey
from sqlalchemy.orm import relationship

from api.app.models.base import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True)  # task_<unique_id>
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    type = Column(String, nullable=False)  # whoami, uptime, shell_execute
    payload = Column(JSON, nullable=False)
    status = Column(String, nullable=False, default="queued")
    attempt_count = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=3)
    run_timeout_seconds = Column(Integer, nullable=False, default=3600)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)
    dispatched_at = Column(String, nullable=True)
    ack_deadline_at = Column(String, nullable=True)
    started_at = Column(String, nullable=True)
    completed_at = Column(String, nullable=True)
    cancel_requested_at = Column(String, nullable=True)
    exit_code = Column(Integer, nullable=True)
    failure_reason = Column(String, nullable=True)
    result_stdout = Column(String, nullable=True)
    result_stderr = Column(String, nullable=True)

    agent = relationship("Agent", foreign_keys=[agent_id])