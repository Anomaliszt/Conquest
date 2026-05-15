import secrets
import hashlib
from api.app.db import get_session
from api.app.models import RegistrationToken
from api.app.utils.time import now_iso


def main():
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    session = get_session()
    try:
        registration_token = RegistrationToken(
            token_hash=token_hash,
            used=0,
            expires_at=None,
            created_at=now_iso(),
        )
        session.add(registration_token)
        session.commit()
    finally:
        session.close()

    print("Registration token:")
    print(token)


if __name__ == "__main__":
    main()