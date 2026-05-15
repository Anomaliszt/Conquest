import uuid
from sqlalchemy import Column, String, JSON, Index
from sqlalchemy.orm import relationship

from api.app.models.base import Base


class OperatorEvent(Base):
    __tablename__ = "operator_events"

    id = Column(String, primary_key=True)  # event_<unique_id>
    cursor = Column(String, nullable=False, unique=True)  # opaque cursor for replay
    event_type = Column(String, nullable=False)  # agent_registered, task_created, etc.
    data = Column(JSON, nullable=False)  # event payload
    created_at = Column(String, nullable=False)

    __table_args__ = (
        Index('ix_operator_events_created_at', 'created_at'),
        Index('ix_operator_events_cursor', 'cursor'),
    )


def generate_event_id():
    return f"event_{uuid.uuid4().hex[:12]}"


def generate_cursor():
    return f"evt_cursor_{uuid.uuid4().hex[:16]}"