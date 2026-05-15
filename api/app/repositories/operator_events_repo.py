from typing import List, Dict, Any

from api.app.db import get_session
from api.app.models.operator_event import OperatorEvent, generate_event_id, generate_cursor
from api.app.utils.time import now_iso


def create_operator_event(event_type: str, data: Dict[str, Any]) -> OperatorEvent:
    """Create and store a new operator event.
    
    Args:
        event_type: Type of event (e.g., 'task_created', 'agent_registered')
        data: Event payload data
        
    Returns:
        Created OperatorEvent instance
    """
    event_id = generate_event_id()
    cursor = generate_cursor()
    created_at = now_iso()

    session = get_session()
    try:
        event = OperatorEvent(
            id=event_id,
            cursor=cursor,
            event_type=event_type,
            data=data,
            created_at=created_at,
        )
        session.add(event)
        session.commit()
        session.refresh(event)
        session.expunge(event)
        return event
    finally:
        session.close()


def get_events_after_cursor(cursor: str, limit: int = 100) -> List[OperatorEvent]:
    """Get events after a specific cursor for replay.
    
    Args:
        cursor: The cursor to start from
        limit: Maximum number of events to return
        
    Returns:
        List of events after the cursor, ordered by creation time
    """
    session = get_session()
    try:
        cursor_event = session.query(OperatorEvent).filter_by(cursor=cursor).first()
        if not cursor_event:
            return []

        events = (
            session.query(OperatorEvent)
            .filter(OperatorEvent.created_at > cursor_event.created_at)
            .order_by(OperatorEvent.created_at.asc())
            .limit(limit)
            .all()
        )
        for e in events:
            session.expunge(e)
        return events
    finally:
        session.close()


def get_events_since_id(event_id: str, limit: int = 100) -> List[OperatorEvent]:
    """Get events after a specific event ID.
    
    Args:
        event_id: The event ID to start from
        limit: Maximum number of events to return
        
    Returns:
        List of events after the given event ID, ordered by creation time
    """
    session = get_session()
    try:
        event = session.query(OperatorEvent).filter_by(id=event_id).first()
        if not event:
            return []

        events = (
            session.query(OperatorEvent)
            .filter(OperatorEvent.created_at > event.created_at)
            .order_by(OperatorEvent.created_at.asc())
            .limit(limit)
            .all()
        )
        for e in events:
            session.expunge(e)
        return events
    finally:
        session.close()


def get_recent_events(limit: int = 100) -> List[OperatorEvent]:
    """Get the most recent operator events.
    
    Args:
        limit: Maximum number of recent events to return
        
    Returns:
        List of recent events ordered by creation time (oldest first)
    """
    session = get_session()
    try:
        events = (
            session.query(OperatorEvent)
            .order_by(OperatorEvent.created_at.desc())
            .limit(limit)
            .all()
        )
        for e in events:
            session.expunge(e)
        return list(reversed(events))
    finally:
        session.close()
