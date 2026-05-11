from sqlalchemy.exc import IntegrityError

from api.app.db.database import get_session
from api.app.models import Operator


def create_operator(operator_id, username, password_hash, status, created_at):
    """Creates a new operator in the database."""
    session = get_session()

    try:
        operator = Operator(
            id=operator_id,
            username=username,
            password_hash=password_hash,
            status=status,
            created_at=created_at,
        )
        session.add(operator)
        session.commit()
    except IntegrityError:
        raise
    finally:
        session.close()


def get_operator_by_username(username):
    """Retrieves an operator by their username."""
    session = get_session()

    try:
        return session.query(Operator).filter(Operator.username == username).first()
    finally:
        session.close()