from api.app.db.database import get_session
from api.app.models import RegistrationToken


def get_registration_token(token_hash):
    """Retrieves a registration token by its hash."""
    session = get_session()

    try:
        return session.query(RegistrationToken).filter(RegistrationToken.token_hash == token_hash).first()
    finally:
        session.close()


def mark_registration_token_used(token_hash, operator_id, used_at):
    """Marks a registration token as used by an operator."""
    session = get_session()

    try:
        token = session.query(RegistrationToken).filter(RegistrationToken.token_hash == token_hash).first()
        if token:
            token.used = 1
            token.used_at = used_at
            token.used_by_operator_id = operator_id
            session.commit()
    finally:
        session.close()