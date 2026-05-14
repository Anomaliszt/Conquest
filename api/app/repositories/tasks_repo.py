from sqlalchemy.exc import IntegrityError

from api.app.db.database import get_session
from api.app.models import Task


def create_task(
    task_id,
    agent_id,
    task_type,
    payload,
    status,
    attempt_count,
    max_attempts,
    run_timeout_seconds,
    created_at,
    updated_at,
):
    session = get_session()
    try:
        task = Task(
            id=task_id,
            agent_id=agent_id,
            type=task_type,
            payload=payload,
            status=status,
            attempt_count=attempt_count,
            max_attempts=max_attempts,
            run_timeout_seconds=run_timeout_seconds,
            created_at=created_at,
            updated_at=updated_at,
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        session.expunge(task)
        return task
    except IntegrityError:
        session.rollback()
        raise
    finally:
        session.close()


def get_task_by_id(task_id):
    session = get_session()
    try:
        return session.query(Task).filter(Task.id == task_id).first()
    finally:
        session.close()


def list_tasks(status=None, agent_id=None, limit=50, offset=0):
    session = get_session()
    try:
        query = session.query(Task)
        if status:
            query = query.filter(Task.status == status)
        if agent_id:
            query = query.filter(Task.agent_id == agent_id)
        tasks = query.order_by(Task.created_at.desc()).limit(limit).offset(offset).all()
        total_count = query.count()
        return tasks, total_count
    finally:
        session.close()


def update_task_status(task_id, new_status, updated_at, **kwargs):
    session = get_session()
    try:
        task = session.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = new_status
            task.updated_at = updated_at
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            session.commit()
            session.refresh(task)
            session.expunge(task)
        return task
    finally:
        session.close()


def get_task_result(task_id):
    session = get_session()
    try:
        task = session.query(Task).filter(Task.id == task_id).first()
        return task
    finally:
        session.close()


def delete_tasks_by_agent(agent_id):
    session = get_session()
    try:
        session.query(Task).filter(Task.agent_id == agent_id).delete()
        session.commit()
    finally:
        session.close()