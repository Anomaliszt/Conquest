import hashlib

from werkzeug.security import generate_password_hash

from api.app.models import Operator, RegistrationToken


def _hash_token(raw_token):
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _insert_registration_token(session, raw_token, expires_at=None, used=0):
    """Inserts a registration token into the database."""
    token = RegistrationToken(
        token_hash=_hash_token(raw_token),
        used=used,
        expires_at=expires_at,
        created_at="2026-01-01T00:00:00+00:00",
    )
    session.add(token)
    session.commit()


def _insert_operator(session, username, password, status="active"):
    """Inserts an operator into the database."""
    operator = Operator(
        id=f"operator_{username}",
        username=username,
        password_hash=generate_password_hash(password),
        status=status,
        created_at="2026-01-01T00:00:00+00:00",
    )
    session.add(operator)
    session.commit()


def test_register_operator_success_matches_contract(client, db_session):
    """Tests that the /api/v1/operator/register endpoint successfully registers an operator and that the response matches the expected contract."""
    registration_token = "a" * 32
    _insert_registration_token(db_session, registration_token)

    response = client.post(
        "/api/v1/operator/register",
        json={
            "registration_token": registration_token,
            "username": "alice",
            "password": "super-secure-password",
        },
    )

    assert response.status_code == 201

    body = response.get_json()
    assert set(body.keys()) == {"data"}

    data = body["data"]
    assert data["id"].startswith("operator_")
    assert data["username"] == "alice"
    assert data["status"] == "active"
    assert "created_at" in data

    token_row = db_session.query(RegistrationToken).filter(
        RegistrationToken.token_hash == _hash_token(registration_token)
    ).first()

    assert token_row.used == 1
    assert token_row.used_by_operator_id == data["id"]


def test_register_operator_rejects_missing_body_fields(client):
    """"Tests that the /api/v1/operator/register endpoint rejects requests with missing required fields."""
    response = client.post("/api/v1/operator/register", json={})

    assert response.status_code == 400
    body = response.get_json()
    
    # Check contract-compliant error response structure
    assert "request_id" in body
    assert body["request_id"]
    assert "error" in body
    
    error = body["error"]
    assert error["code"] == "BAD_REQUEST"
    assert error["message"] == "Invalid request payload"
    assert "details" in error
    
    # Check that all required fields are mentioned in the validation errors
    required_fields = {"registration_token", "username", "password"}
    error_fields = {detail["field"] for detail in error["details"]}
    assert required_fields.issubset(error_fields)


def test_register_operator_rejects_invalid_token(client):
    response = client.post(
        "/api/v1/operator/register",
        json={
            "registration_token": "a" * 32,
            "username": "alice",
            "password": "super-secure-password",
        },
    )

    assert response.status_code == 401
    body = response.get_json()
    assert "request_id" in body
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert body["error"]["message"] == "invalid registration token"


def test_register_operator_rejects_reused_token(client, db_session):
    registration_token = "b" * 32
    _insert_registration_token(db_session, registration_token, used=1)

    response = client.post(
        "/api/v1/operator/register",
        json={
            "registration_token": registration_token,
            "username": "alice",
            "password": "super-secure-password",
        },
    )

    assert response.status_code == 401
    body = response.get_json()
    assert "request_id" in body
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert body["error"]["message"] == "registration token already used"


def test_register_operator_rejects_duplicate_username(client, db_session):
    registration_token = "c" * 32
    _insert_registration_token(db_session, registration_token)
    _insert_operator(db_session, "alice", "super-secure-password")

    response = client.post(
        "/api/v1/operator/register",
        json={
            "registration_token": registration_token,
            "username": "alice",
            "password": "another-secure-password",
        },
    )

    assert response.status_code == 409
    body = response.get_json()
    assert "request_id" in body
    assert body["error"]["code"] == "CONFLICT"
    assert body["error"]["message"] == "username already exists"


def test_login_operator_success_matches_contract(client, db_session):
    _insert_operator(db_session, "alice", "super-secure-password")

    response = client.post(
        "/api/v1/operator/login",
        json={
            "username": "alice",
            "password": "super-secure-password",
        },
    )

    assert response.status_code == 200

    body = response.get_json()
    assert set(body.keys()) == {"data"}

    data = body["data"]
    assert data["operator_id"] == "operator_alice"
    assert data["token_type"] == "Bearer"
    assert data["expires_in"] == 900
    assert isinstance(data["operator_token"], str)
    assert data["operator_token"]


def test_login_operator_rejects_invalid_credentials(client, db_session):
    _insert_operator(db_session, "alice", "super-secure-password")

    response = client.post(
        "/api/v1/operator/login",
        json={
            "username": "alice",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    body = response.get_json()
    assert "request_id" in body
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert body["error"]["message"] == "invalid username or password"


def test_login_operator_rejects_disabled_operator(client, db_session):
    _insert_operator(
        db_session,
        "alice",
        "super-secure-password",
        status="disabled",
    )

    response = client.post(
        "/api/v1/operator/login",
        json={
            "username": "alice",
            "password": "super-secure-password",
        },
    )

    assert response.status_code == 401
    body = response.get_json()
    assert "request_id" in body
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert body["error"]["message"] == "operator account is disabled"