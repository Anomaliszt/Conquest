import secrets
import hashlib
from api.app.db.sqlite import get_connection
from api.app.utils.time import now_iso


def main():
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    conn = get_connection()
    conn.execute(
        """
        INSERT INTO operator_registration_tokens
            (token_hash, used, expires_at, created_at)
        VALUES (?, 0, NULL, ?)
        """,
        (token_hash, now_iso()),
    )
    conn.commit()
    conn.close()

    print("Registration token:")
    print(token)


if __name__ == "__main__":
    main()