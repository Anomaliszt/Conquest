import pytest
from werkzeug.security import generate_password_hash

from api.app.services import operator_service


class MockToken:
    def __init__(self, used, expires_at):
        self.used = used
        self.expires_at = expires_at


class MockOperator:
    def __init__(self, id, username, password_hash, status):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.status = status


def test_hash_registration_token_is_sha256_hex():
    token = "a" * 32

    hashed = operator_service.hash_registration_token(token)

    assert len(hashed) == 64
    assert hashed == operator_service.hash_registration_token(token)
    assert hashed != token


@pytest.mark.parametrize(
    ("token_response", "username", "password", "expected_error", "expected_status"),
    [
        # Token not found
        (None, "alice", "super-secure-password", "invalid registration token", 401),
        # Token already used
        (MockToken(used=1, expires_at=None), "alice", "super-secure-password", "registration token already used", 401),
        # Token expired
        (MockToken(used=0, expires_at="2000-01-01T00:00:00+00:00"), "alice", "super-secure-password", "registration token expired", 401),
    ],
)
def test_register_operator_validates_business_logic(
    monkeypatch,
    token_response,
    username,
    password,
    expected_error,
    expected_status,
):
    monkeypatch.setattr(
        operator_service,
        "get_registration_token",
        lambda token_hash: token_response,
    )

    result, error = operator_service.register_operator(
        registration_token="a" * 32,
        username=username,
        password=password,
    )

    assert result is None
    assert error == (expected_error, expected_status)


def test_register_operator_success_creates_operator_and_marks_token_used(monkeypatch):
    created = {}
    marked = {}

    monkeypatch.setattr(
        operator_service,
        "get_registration_token",
        lambda token_hash: MockToken(used=0, expires_at=None),
    )
    monkeypatch.setattr(operator_service, "now_iso", lambda: "2026-01-01T00:00:00+00:00")

    def fake_create_operator(**kwargs):
        created.update(kwargs)

    def fake_mark_registration_token_used(**kwargs):
        marked.update(kwargs)

    monkeypatch.setattr(operator_service, "create_operator", fake_create_operator)
    monkeypatch.setattr(operator_service, "mark_registration_token_used", fake_mark_registration_token_used)

    result, error = operator_service.register_operator(
        registration_token="a" * 32,
        username="alice",
        password="super-secure-password",
    )

    assert error is None
    assert result["id"].startswith("operator_")
    assert result["username"] == "alice"
    assert result["status"] == "active"
    assert result["created_at"] == "2026-01-01T00:00:00+00:00"

    assert created["operator_id"] == result["id"]
    assert created["username"] == "alice"
    assert created["status"] == "active"
    assert created["created_at"] == "2026-01-01T00:00:00+00:00"
    assert created["password_hash"] != "super-secure-password"

    assert marked["operator_id"] == result["id"]
    assert marked["used_at"] == "2026-01-01T00:00:00+00:00"


def test_register_operator_maps_unique_username_error_to_conflict(monkeypatch):
    monkeypatch.setattr(
        operator_service,
        "get_registration_token",
        lambda token_hash: MockToken(used=0, expires_at=None),
    )

    def raise_integrity_error(**kwargs):
        from sqlalchemy.exc import IntegrityError
        raise IntegrityError(None, None, None)

    monkeypatch.setattr(operator_service, "create_operator", raise_integrity_error)

    result, error = operator_service.register_operator(
        registration_token="a" * 32,
        username="alice",
        password="super-secure-password",
    )

    assert result is None
    assert error == ("username already exists", 409)


def test_login_operator_rejects_unknown_username(monkeypatch):
    monkeypatch.setattr(operator_service, "get_operator_by_username", lambda username: None)

    result, error = operator_service.login_operator(
        username="alice",
        password="super-secure-password",
    )

    assert result is None
    assert error == ("invalid username or password", 401)


def test_login_operator_rejects_disabled_operator(monkeypatch):
    monkeypatch.setattr(
        operator_service,
        "get_operator_by_username",
        lambda username: MockOperator(
            id="operator_1",
            username=username,
            password_hash=generate_password_hash("super-secure-password"),
            status="disabled",
        ),
    )

    result, error = operator_service.login_operator(
        username="alice",
        password="super-secure-password",
    )

    assert result is None
    assert error == ("operator account is disabled", 401)


def test_login_operator_rejects_wrong_password(monkeypatch):
    monkeypatch.setattr(
        operator_service,
        "get_operator_by_username",
        lambda username: MockOperator(
            id="operator_1",
            username=username,
            password_hash=generate_password_hash("super-secure-password"),
            status="active",
        ),
    )

    result, error = operator_service.login_operator(
        username="alice",
        password="wrong-password",
    )

    assert result is None
    assert error == ("invalid username or password", 401)


def test_login_operator_success_returns_bearer_token(monkeypatch):
    monkeypatch.setattr(
        operator_service,
        "get_operator_by_username",
        lambda username: MockOperator(
            id="operator_1",
            username=username,
            password_hash=generate_password_hash("super-secure-password"),
            status="active",
        ),
    )
    monkeypatch.setattr(operator_service, "create_operator_token", lambda operator_id: "jwt-token")

    result, error = operator_service.login_operator(
        username="alice",
        password="super-secure-password",
    )

    assert error is None
    assert result == {
        "operator_id": "operator_1",
        "operator_token": "jwt-token",
        "token_type": "Bearer",
        "expires_in": 900,
    }