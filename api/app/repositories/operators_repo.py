import sqlite3
from api.app.db.sqlite import get_connection


def create_operator(operator_id, username, password_hash, status, created_at):
    conn = get_connection()

    try:
        conn.execute(
            """
            INSERT INTO operators (id, username, password_hash, status, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (operator_id, username, password_hash, status, created_at),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise
    finally:
        conn.close()


def get_operator_by_username(username):
    conn = get_connection()

    try:
        return conn.execute(
            """
            SELECT id, username, password_hash, status, created_at
            FROM operators
            WHERE username = ?
            """,
            (username,),
        ).fetchone()
    finally:
        conn.close()