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
    """Hash registration token using SHA-256.
    
    Args:
        registration_token: Raw registration token string (min 32 chars)
        
    Returns:
        64-character hex string (SHA-256 hash)
    """
    return hashlib.sha256(registration_token.encode("utf-8")).hexdigest()



def register_operator(registration_token, username, password):
    """Register a new operator using a registration token.
    
    Args:
        registration_token: Registration token (validated by Pydantic: min 32 chars)
        username: Operator username (validated by Pydantic: min 3 chars)
        password: Operator password (validated by Pydantic: min 12 chars)
        
    Returns:
        (dict, None): On success with operator details
        (None, (str, int)): On error with (message, http_status_code)
    
    Error cases (return specific status codes for client handling):
    - 401: Token not found, already used, or expired
    - 409: Username already exists (database constraint)
    """
    # Hash token for database lookup
    token_hash = hash_registration_token(registration_token)
    token_row = get_registration_token(token_hash)

    # Validate token status (exists, unused, not expired)
    if token_row is None:
        return None, ("invalid registration token", 401)

    if token_row["used"] == 1:
        return None, ("registration token already used", 401)

    if is_expired(token_row["expires_at"]):
        return None, ("registration token expired", 401)

    # Generate unique operator ID and hash password securely
    operator_id = f"operator_{uuid.uuid4().hex[:12]}"  # Format: operator_<12 random hex chars>
    password_hash = generate_password_hash(password)  # Uses Werkzeug secure hashing
    created_at = now_iso()  # ISO 8601 timestamp with timezone

    # Create operator and mark token as used in a single transaction to ensure consistency
    try:
        # Create the operator account
        create_operator(
            operator_id=operator_id,
            username=username,
            password_hash=password_hash,
            status="active",
            created_at=created_at,
        )

        # Mark registration token as used, linking it to the operator
        mark_registration_token_used(
            token_hash=token_hash,
            operator_id=operator_id,
            used_at=created_at,
        )

    except sqlite3.IntegrityError:
        # Database constraint violation (most likely: unique username)
        return None, ("username already exists", 409)

    # Return created operator details for response
    return {
        "id": operator_id,
        "username": username,
        "status": "active",
        "created_at": created_at,
    }, None


def login_operator(username, password):
    """Authenticate an operator and generate JWT token.
    
    Args:
        username: Operator username (validated by Pydantic: required)
        password: Operator password (validated by Pydantic: required)
        
    Returns:
        (dict, None): On success with token and operator details
        (None, (str, int)): On error with (message, http_status_code)
        
    Security note: Generic error messages ("invalid username or password")
    prevent username enumeration attacks.
    """
    # Look up operator by username
    operator = get_operator_by_username(username)

    # Verify operator exists (generic error for security)
    if operator is None:
        return None, ("invalid username or password", 401)

    # Check account is active (disabled accounts cannot login)
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