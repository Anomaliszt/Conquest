import hashlib

from werkzeug.security import generate_password_hash


def _hash_token(raw_token):
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _insert_registration_token(conn, raw_token, expires_at=None, used=0):
    conn.execute(
        """
        INSERT INTO operator_registration_tokens
            (token_hash, used, expires_at, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            _hash_token(raw_token),
            used,
            expires_at,
            "2026-01-01T00:00:00+00:00",
        ),
    )
    conn.commit()


def _insert_operator(conn, username, password, status="active"):
    conn.execute(
        """
        INSERT INTO operators
            (id, username, password_hash, status, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            f"operator_{username}",
            username,
            generate_password_hash(password),
            status,
            "2026-01-01T00:00:00+00:00",
        ),
    )
    conn.commit()


def test_register_operator_success_matches_contract(client, db_connection):
    registration_token = "a" * 32
    _insert_registration_token(db_connection, registration_token)

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

    token_row = db_connection.execute(
        """
        SELECT used, used_by_operator_id
        FROM operator_registration_tokens
        WHERE token_hash = ?
        """,
        (_hash_token(registration_token),),
    ).fetchone()

    assert token_row["used"] == 1
    assert token_row["used_by_operator_id"] == data["id"]


def test_register_operator_rejects_missing_body_fields(client):
    response = client.post("/api/v1/operator/register", json={})

    assert response.status_code == 400
    assert response.get_json() == {"error": "registration_token is required"}


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
    assert response.get_json() == {"error": "invalid registration token"}


def test_register_operator_rejects_reused_token(client, db_connection):
    registration_token = "b" * 32
    _insert_registration_token(db_connection, registration_token, used=1)

    response = client.post(
        "/api/v1/operator/register",
        json={
            "registration_token": registration_token,
            "username": "alice",
            "password": "super-secure-password",
        },
    )

    assert response.status_code == 401
    assert response.get_json() == {"error": "registration token already used"}


def test_register_operator_rejects_duplicate_username(client, db_connection):
    registration_token = "c" * 32
    _insert_registration_token(db_connection, registration_token)
    _insert_operator(db_connection, "alice", "super-secure-password")

    response = client.post(
        "/api/v1/operator/register",
        json={
            "registration_token": registration_token,
            "username": "alice",
            "password": "another-secure-password",
        },
    )

    assert response.status_code == 409
    assert response.get_json() == {"error": "username already exists"}


def test_login_operator_success_matches_contract(client, db_connection):
    _insert_operator(db_connection, "alice", "super-secure-password")

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


def test_login_operator_rejects_invalid_credentials(client, db_connection):
    _insert_operator(db_connection, "alice", "super-secure-password")

    response = client.post(
        "/api/v1/operator/login",
        json={
            "username": "alice",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.get_json() == {"error": "invalid username or password"}


def test_login_operator_rejects_disabled_operator(client, db_connection):
    _insert_operator(
        db_connection,
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
    assert response.get_json() == {"error": "operator account is disabled"}