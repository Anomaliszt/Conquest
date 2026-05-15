import logging
import threading
import time
from datetime import datetime, timezone

from api.app.repositories.tasks_repo import list_tasks, update_task_status
from api.app.utils.time import now_iso
from api.app.ws import socketio
from api.app.ws.events import emit_operator_event

logger = logging.getLogger(__name__)


def check_deadlines():
    while True:
        try:
            _check_task_deadlines()
        except Exception as e:
            logger.error("Deadline check error: %s", e)
        time.sleep(10)


def _check_task_deadlines():
    now = datetime.now(timezone.utc).isoformat()

    dispatched_tasks, _ = list_tasks(status="dispatched", limit=1000)
    for task in dispatched_tasks:
        if task.ack_deadline_at and task.ack_deadline_at < now:
            update_task_status(task.id, "orphaned", now_iso())
            emit_operator_event(socketio, "task_orphaned", {
                "task_id": task.id,
                "agent_id": task.agent_id,
                "reason": "Ack deadline exceeded",
            })

    running_tasks, _ = list_tasks(status="running", limit=1000)
    for task in running_tasks:
        if task.run_deadline_at and task.run_deadline_at < now:
            update_task_status(task.id, "orphaned", now_iso())
            emit_operator_event(socketio, "task_orphaned", {
                "task_id": task.id,
                "agent_id": task.agent_id,
                "reason": "Run deadline exceeded",
            })


def start_deadline_checker():
    thread = threading.Thread(target=check_deadlines, daemon=True)
    thread.start()