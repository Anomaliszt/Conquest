import hashlib
import sqlite3
import uuid
from api.app.utils.time import now_iso, is_expired
from api.app.core.jwt import create_operator_token
from werkzeug.security import generate_password_hash, check_password_hash
from api.app.repositories.operators_repo import (
    create_operator,
    get_operator_by_username,
)
from api.app.repositories.registration_tokens_repo import (
    get_registration_token,
    mark_registration_token_used,
)

def hash_registration_token(registration_token):
    return hashlib.sha256(registration_token.encode("utf-8")).hexdigest()



def register_operator(registration_token, username, password):
    if not registration_token:
        return None, ("registration_token is required", 400)

    if not username:
        return None, ("username is required", 400)

    if not password:
        return None, ("password is required", 400)

    if len(registration_token) < 32:
        return None, ("invalid registration token", 401)

    if len(username) < 3:
        return None, ("username must be at least 3 characters", 400)

    if len(password) < 12:
        return None, ("password must be at least 12 characters", 400)

    token_hash = hash_registration_token(registration_token)
    token_row = get_registration_token(token_hash)

    if token_row is None:
        return None, ("invalid registration token", 401)

    if token_row["used"] == 1:
        return None, ("registration token already used", 401)

    if is_expired(token_row["expires_at"]):
        return None, ("registration token expired", 401)

    operator_id = f"operator_{uuid.uuid4().hex[:12]}"
    password_hash = generate_password_hash(password)
    created_at = now_iso()

    try:
        create_operator(
            operator_id=operator_id,
            username=username,
            password_hash=password_hash,
            status="active",
            created_at=created_at,
        )

        mark_registration_token_used(
            token_hash=token_hash,
            operator_id=operator_id,
            used_at=created_at,
        )

    except sqlite3.IntegrityError:
        return None, ("username already exists", 409)

    return {
        "id": operator_id,
        "username": username,
        "status": "active",
        "created_at": created_at,
    }, None


def login_operator(username, password):
    if not username:
        return None, ("username is required", 400)

    if not password:
        return None, ("password is required", 400)

    operator = get_operator_by_username(username)

    if operator is None:
        return None, ("invalid username or password", 401)

    if operator["status"] != "active":
        return None, ("operator account is disabled", 401)

    if not check_password_hash(operator["password_hash"], password):
        return None, ("invalid username or password", 401)

    return {
        "operator_id": operator["id"],
        "operator_token": create_operator_token(operator["id"]),
        "token_type": "Bearer",
        "expires_in": 900,
    }, None