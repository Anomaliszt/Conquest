import hashlib

from api.app.models import Agent, Task
from api.app.utils.time import now_iso


def _insert_agent(db_session, agent_id="agent_001", status="online"):
    agent = Agent(
        id=agent_id,
        hostname="test-host",
        os="Linux",
        user="root",
        version="1.0.0",
        status=status,
        last_seen=now_iso(),
        created_at=now_iso(),
    )
    db_session.add(agent)
    db_session.commit()
    return agent


def _insert_task(db_session, task_id="task_abc123", agent_id="agent_001", task_type="whoami", status="queued"):
    task = Task(
        id=task_id,
        agent_id=agent_id,
        type=task_type,
        payload={},
        status=status,
        attempt_count=0,
        max_attempts=3,
        run_timeout_seconds=3600,
        created_at=now_iso(),
        updated_at=now_iso(),
    )
    db_session.add(task)
    db_session.commit()
    return task


def _get_operator_token(client, db_session):
    from api.app.models import Operator, RegistrationToken
    from werkzeug.security import generate_password_hash

    token = RegistrationToken(
        token_hash=hashlib.sha256("test_token_12345678901234567890".encode()).hexdigest(),
        used=0,
        expires_at=None,
        created_at=now_iso(),
    )
    db_session.add(token)
    operator = Operator(
        id="operator_test",
        username="testop",
        password_hash=generate_password_hash("testpassword123"),
        status="active",
        created_at=now_iso(),
    )
    db_session.add(operator)
    db_session.commit()

    response = client.post(
        "/api/v1/operator/login",
        json={"username": "testop", "password": "testpassword123"},
    )
    return response.get_json()["data"]["operator_token"]


class TestCreateTask:
    def test_create_whoami_task(self, client, db_session):
        _insert_agent(db_session)
        token = _get_operator_token(client, db_session)

        response = client.post(
            "/api/v1/agents/agent_001/tasks",
            headers={"Authorization": f"Bearer {token}"},
            json={"type": "whoami", "payload": {}},
        )

        assert response.status_code == 201
        data = response.get_json()["data"]
        assert data["type"] == "whoami"
        assert data["status"] == "queued"
        assert data["agent_id"] == "agent_001"

    def test_create_uptime_task(self, client, db_session):
        _insert_agent(db_session)
        token = _get_operator_token(client, db_session)

        response = client.post(
            "/api/v1/agents/agent_001/tasks",
            headers={"Authorization": f"Bearer {token}"},
            json={"type": "uptime", "payload": {}},
        )

        assert response.status_code == 201
        assert response.get_json()["data"]["type"] == "uptime"

    def test_create_shell_execute_task(self, client, db_session):
        _insert_agent(db_session)
        token = _get_operator_token(client, db_session)

        response = client.post(
            "/api/v1/agents/agent_001/tasks",
            headers={"Authorization": f"Bearer {token}"},
            json={"type": "shell_execute", "payload": {"command": "ls", "args": ["-la"]}},
        )

        assert response.status_code == 201
        data = response.get_json()["data"]
        assert data["type"] == "shell_execute"
        assert data["payload"]["command"] == "ls"

    def test_create_task_for_nonexistent_agent(self, client, db_session):
        token = _get_operator_token(client, db_session)

        response = client.post(
            "/api/v1/agents/agent_nonexistent/tasks",
            headers={"Authorization": f"Bearer {token}"},
            json={"type": "whoami", "payload": {}},
        )

        assert response.status_code == 404
        assert response.get_json()["error"]["code"] == "NOT_FOUND"

    def test_create_task_with_invalid_type(self, client, db_session):
        _insert_agent(db_session)
        token = _get_operator_token(client, db_session)

        response = client.post(
            "/api/v1/agents/agent_001/tasks",
            headers={"Authorization": f"Bearer {token}"},
            json={"type": "invalid", "payload": {}},
        )

        assert response.status_code == 400

    def test_create_whoami_with_payload_fails(self, client, db_session):
        _insert_agent(db_session)
        token = _get_operator_token(client, db_session)

        response = client.post(
            "/api/v1/agents/agent_001/tasks",
            headers={"Authorization": f"Bearer {token}"},
            json={"type": "whoami", "payload": {"extra": "data"}},
        )

        assert response.status_code == 400
        assert "does not accept payload" in response.get_json()["error"]["message"]

    def test_create_shell_execute_without_command_fails(self, client, db_session):
        _insert_agent(db_session)
        token = _get_operator_token(client, db_session)

        response = client.post(
            "/api/v1/agents/agent_001/tasks",
            headers={"Authorization": f"Bearer {token}"},
            json={"type": "shell_execute", "payload": {}},
        )

        assert response.status_code == 400
        assert "requires 'command'" in response.get_json()["error"]["message"]

    def test_create_task_requires_auth(self, client, db_session):
        _insert_agent(db_session)

        response = client.post(
            "/api/v1/agents/agent_001/tasks",
            json={"type": "whoami", "payload": {}},
        )

        assert response.status_code == 401


class TestListTasks:
    def test_list_tasks(self, client, db_session):
        _insert_agent(db_session)
        _insert_task(db_session, "task_001", "agent_001", "whoami")
        _insert_task(db_session, "task_002", "agent_001", "uptime")
        token = _get_operator_token(client, db_session)

        response = client.get(
            "/api/v1/tasks",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["data"]) == 2
        assert "pagination" in data

    def test_list_tasks_with_status_filter(self, client, db_session):
        _insert_agent(db_session)
        _insert_task(db_session, "task_001", "agent_001", "whoami", "queued")
        _insert_task(db_session, "task_002", "agent_001", "uptime", "completed")
        token = _get_operator_token(client, db_session)

        response = client.get(
            "/api/v1/tasks?status=completed",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()["data"]
        assert len(data) == 1
        assert data[0]["status"] == "completed"

    def test_list_tasks_requires_auth(self, client, db_session):
        response = client.get("/api/v1/tasks")
        assert response.status_code == 401


class TestGetTask:
    def test_get_task(self, client, db_session):
        _insert_agent(db_session)
        _insert_task(db_session, "task_001", "agent_001", "whoami")
        token = _get_operator_token(client, db_session)

        response = client.get(
            "/api/v1/tasks/task_001",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.get_json()["data"]["id"] == "task_001"

    def test_get_nonexistent_task(self, client, db_session):
        token = _get_operator_token(client, db_session)

        response = client.get(
            "/api/v1/tasks/task_nonexistent",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404


class TestCancelTask:
    def test_cancel_queued_task(self, client, db_session):
        _insert_agent(db_session)
        _insert_task(db_session, "task_001", "agent_001", "whoami", "queued")
        token = _get_operator_token(client, db_session)

        response = client.post(
            "/api/v1/tasks/task_001/cancel",
            headers={"Authorization": f"Bearer {token}"},
            json={"reason": "testing", "grace_period_seconds": 10},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "cancelled"

    def test_cancel_running_task(self, client, db_session):
        _insert_agent(db_session)
        _insert_task(db_session, "task_001", "agent_001", "whoami", "running")
        token = _get_operator_token(client, db_session)

        response = client.post(
            "/api/v1/tasks/task_001/cancel",
            headers={"Authorization": f"Bearer {token}"},
            json={"reason": "testing"},
        )

        assert response.status_code == 200
        assert response.get_json()["status"] == "cancellation_requested"

    def test_cancel_completed_task_fails(self, client, db_session):
        _insert_agent(db_session)
        _insert_task(db_session, "task_001", "agent_001", "whoami", "completed")
        token = _get_operator_token(client, db_session)

        response = client.post(
            "/api/v1/tasks/task_001/cancel",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )

        assert response.status_code == 409


class TestGetTaskResult:
    def test_get_result_for_completed_task(self, client, db_session):
        _insert_agent(db_session)
        task = _insert_task(db_session, "task_001", "agent_001", "whoami", "completed")
        task.result_stdout = "root"
        task.exit_code = 0
        db_session.commit()

        token = _get_operator_token(client, db_session)

        response = client.get(
            "/api/v1/tasks/task_001/result",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.get_json()["data"]["stdout"] == "root"

    def test_get_result_for_queued_task(self, client, db_session):
        _insert_agent(db_session)
        _insert_task(db_session, "task_001", "agent_001", "whoami", "queued")
        token = _get_operator_token(client, db_session)

        response = client.get(
            "/api/v1/tasks/task_001/result",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404


class TestSendAllTasks:
    def test_send_all_dry_run(self, client, db_session):
        _insert_agent(db_session, "agent_001")
        _insert_agent(db_session, "agent_002")
        token = _get_operator_token(client, db_session)

        response = client.post(
            "/api/v1/tasks/send-all",
            headers={"Authorization": f"Bearer {token}"},
            json={"type": "uptime", "payload": {}, "dry_run": True},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "agent_001" in data["task_ids"]
        assert "agent_002" in data["task_ids"]

    def test_send_all_creates_tasks(self, client, db_session):
        _insert_agent(db_session, "agent_001")
        token = _get_operator_token(client, db_session)

        response = client.post(
            "/api/v1/tasks/send-all",
            headers={"Authorization": f"Bearer {token}"},
            json={"type": "whoami", "payload": {}},
        )

        assert response.status_code == 202
        data = response.get_json()
        assert data["count"] == 1


class TestTaskHistory:
    def test_task_history(self, client, db_session):
        _insert_agent(db_session)
        _insert_task(db_session, "task_001", "agent_001", "whoami")
        token = _get_operator_token(client, db_session)

        response = client.get(
            "/api/v1/task-history",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["data"]) >= 1
        assert "task_id" in data["data"][0]
        assert "pagination" in data