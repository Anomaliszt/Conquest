from api.app.db.sqlite import get_connection


def get_registration_token(token_hash):
    """Retrieves a registration token by its hash."""
    conn = get_connection()

    try:
        return conn.execute(
            """
            SELECT token_hash, used, expires_at, created_at, used_at, used_by_operator_id
            FROM operator_registration_tokens
            WHERE token_hash = ?
            """,
            (token_hash,),
        ).fetchone()
    finally:
        conn.close()


def mark_registration_token_used(token_hash, operator_id, used_at):
    """Marks a registration token as used by an operator."""
    conn = get_connection()

    try:
        conn.execute(
            """
            UPDATE operator_registration_tokens
            SET used = 1,
                used_at = ?,
                used_by_operator_id = ?
            WHERE token_hash = ?
            """,
            (used_at, operator_id, token_hash),
        )
        conn.commit()
    finally:
        conn.close()