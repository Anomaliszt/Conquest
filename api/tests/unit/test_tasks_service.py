import pytest

from api.app.services.tasks_service import (
    TaskCommand,
    create_task_for_agent,
    get_task,
    list_all_tasks,
    cancel_task,
    get_result,
)


class MockAgent:
    def __init__(self, id, status):
        self.id = id
        self.status = status


class MockTask:
    def __init__(self, id, status, result_stdout=None, exit_code=None, result_stderr=None, failure_reason=None):
        self.id = id
        self.status = status
        self.result_stdout = result_stdout
        self.result_stderr = result_stderr
        self.exit_code = exit_code
        self.failure_reason = failure_reason


class TestTaskCommand:
    def test_whoami_does_not_accept_payload(self):
        assert TaskCommand.WHOAMI.accepts_payload() is False

    def test_uptime_does_not_accept_payload(self):
        assert TaskCommand.UPTIME.accepts_payload() is False

    def test_shell_execute_accepts_payload(self):
        assert TaskCommand.SHELL_EXECUTE.accepts_payload() is True

    def test_command_string_value(self):
        assert TaskCommand.WHOAMI == "whoami"
        assert TaskCommand.UPTIME == "uptime"
        assert TaskCommand.SHELL_EXECUTE == "shell_execute"

    def test_invalid_command_raises(self):
        with pytest.raises(ValueError):
            TaskCommand("invalid")


class TestCreateTaskForAgent:
    def test_creates_task_with_valid_command(self, monkeypatch):
        created_kwargs = {}

        def fake_create_task(**kwargs):
            created_kwargs.update(kwargs)
            result = type("CreatedTask", (), kwargs)()
            return result

        monkeypatch.setattr("api.app.services.tasks_service.get_agent_by_id", lambda id: MockAgent(id, "online"))
        monkeypatch.setattr("api.app.services.tasks_service.create_task", fake_create_task)

        result, error = create_task_for_agent(
            agent_id="agent_001",
            task_type="whoami",
            payload={},
        )

        assert error is None
        assert created_kwargs["task_type"] == "whoami"
        assert created_kwargs["status"] == "queued"

    def test_rejects_shell_execute_with_command_in_payload(self, monkeypatch):
        created_task = None

        def fake_create_task(**kwargs):
            nonlocal created_task
            created_task = type("Task", (), kwargs)
            return created_task

        monkeypatch.setattr("api.app.services.tasks_service.get_agent_by_id", lambda id: MockAgent(id, "online"))
        monkeypatch.setattr("api.app.services.tasks_service.create_task", fake_create_task)

        result, error = create_task_for_agent(
            agent_id="agent_001",
            task_type="shell_execute",
            payload={"command": "ls"},
        )

        assert error is None
        assert created_task.payload["command"] == "ls"

    def test_rejects_invalid_task_type(self, monkeypatch):
        result, error = create_task_for_agent(
            agent_id="agent_001",
            task_type="invalid_command",
            payload={},
        )

        assert result is None
        assert error[1] == 422

    def test_returns_404_for_nonexistent_agent(self, monkeypatch):
        monkeypatch.setattr("api.app.services.tasks_service.get_agent_by_id", lambda id: None)

        result, error = create_task_for_agent(
            agent_id="agent_nonexistent",
            task_type="whoami",
            payload={},
        )

        assert result is None
        assert error == ("agent not found", 404)

    def test_rejects_task_for_decommissioned_agent(self, monkeypatch):
        monkeypatch.setattr("api.app.services.tasks_service.get_agent_by_id", lambda id: MockAgent(id, "decommissioned"))

        result, error = create_task_for_agent(
            agent_id="agent_001",
            task_type="whoami",
            payload={},
        )

        assert result is None
        assert error == ("agent not available for tasks", 400)

    def test_rejects_whoami_with_payload(self, monkeypatch):
        monkeypatch.setattr("api.app.services.tasks_service.get_agent_by_id", lambda id: MockAgent(id, "online"))

        result, error = create_task_for_agent(
            agent_id="agent_001",
            task_type="whoami",
            payload={"extra": "data"},
        )

        assert result is None
        assert "does not accept payload" in error[0]

    def test_rejects_shell_execute_without_command(self, monkeypatch):
        monkeypatch.setattr("api.app.services.tasks_service.get_agent_by_id", lambda id: MockAgent(id, "online"))

        result, error = create_task_for_agent(
            agent_id="agent_001",
            task_type="shell_execute",
            payload={},
        )

        assert result is None
        assert "requires 'command'" in error[0]


class TestGetTask:
    def test_returns_task_when_exists(self, monkeypatch):
        mock_task = MockTask("task_001", "queued")
        monkeypatch.setattr("api.app.services.tasks_service.get_task_by_id", lambda id: mock_task)

        result = get_task("task_001")

        assert result == mock_task

    def test_returns_none_for_nonexistent_task(self, monkeypatch):
        monkeypatch.setattr("api.app.services.tasks_service.get_task_by_id", lambda id: None)

        result = get_task("task_nonexistent")

        assert result is None


class TestListAllTasks:
    def test_returns_tasks_list(self, monkeypatch):
        mock_tasks = [MockTask("task_001", "queued"), MockTask("task_002", "completed")]
        monkeypatch.setattr("api.app.services.tasks_service.list_tasks", lambda **kw: (mock_tasks, 2))

        tasks, total = list_all_tasks()

        assert len(tasks) == 2
        assert total == 2

    def test_passes_filters(self, monkeypatch):
        captured_kwargs = {}

        def fake_list_tasks(status=None, agent_id=None, limit=50, offset=0):
            captured_kwargs["status"] = status
            captured_kwargs["agent_id"] = agent_id
            captured_kwargs["limit"] = limit
            captured_kwargs["offset"] = offset
            return [], 0

        monkeypatch.setattr("api.app.services.tasks_service.list_tasks", fake_list_tasks)

        list_all_tasks(status="completed", agent_id="agent_001", limit=10, offset=5)

        assert captured_kwargs == {"status": "completed", "agent_id": "agent_001", "limit": 10, "offset": 5}


class TestCancelTask:
    def test_cancels_queued_task(self, monkeypatch):
        mock_task = MockTask("task_001", "queued")
        monkeypatch.setattr("api.app.services.tasks_service.get_task_by_id", lambda id: mock_task)
        monkeypatch.setattr(
            "api.app.services.tasks_service.update_task_status",
            lambda task_id, new_status, updated_at, **kw: type("Task", (), {"id": task_id, "status": new_status})()
        )

        result, error = cancel_task("task_001")

        assert error is None
        assert result.status == "cancelled"

    def test_requests_cancellation_for_running_task(self, monkeypatch):
        mock_task = MockTask("task_001", "running")
        monkeypatch.setattr("api.app.services.tasks_service.get_task_by_id", lambda id: mock_task)
        monkeypatch.setattr(
            "api.app.services.tasks_service.update_task_status",
            lambda task_id, new_status, updated_at, **kw: type("Task", (), {"id": task_id, "status": new_status})()
        )

        result, error = cancel_task("task_001")

        assert error is None
        assert result.status == "cancellation_requested"

    def test_rejects_cancellation_of_completed_task(self, monkeypatch):
        mock_task = MockTask("task_001", "completed")
        monkeypatch.setattr("api.app.services.tasks_service.get_task_by_id", lambda id: mock_task)

        result, error = cancel_task("task_001")

        assert result is None
        assert error[1] == 409

    def test_returns_404_for_nonexistent_task(self, monkeypatch):
        monkeypatch.setattr("api.app.services.tasks_service.get_task_by_id", lambda id: None)

        result, error = cancel_task("task_nonexistent")

        assert result is None
        assert error == ("task not found", 404)


class TestGetResult:
    def test_returns_result_for_completed_task(self, monkeypatch):
        mock_task = MockTask("task_001", "completed", result_stdout="root", exit_code=0, result_stderr=None)
        monkeypatch.setattr("api.app.services.tasks_service.get_task_result", lambda id: mock_task)

        result, error = get_result("task_001")

        assert error is None
        assert result["stdout"] == "root"
        assert result["exit_code"] == 0

    def test_returns_404_for_queued_task(self, monkeypatch):
        mock_task = MockTask("task_001", "queued")
        monkeypatch.setattr("api.app.services.tasks_service.get_task_result", lambda id: mock_task)

        result, error = get_result("task_001")

        assert result is None
        assert "not available yet" in error[0]

    def test_returns_404_for_nonexistent_task(self, monkeypatch):
        monkeypatch.setattr("api.app.services.tasks_service.get_task_result", lambda id: None)

        result, error = get_result("task_nonexistent")

        assert result is None
        assert error == ("task not found", 404)