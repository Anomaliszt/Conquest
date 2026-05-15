import os
import sys
from pathlib import Path

import pytest

API_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = API_DIR.parent

sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture()
def app():
    from api.app.main import create_app

    app = create_app(testing=True)
    return app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db_session():
    from api.app.db import get_session
    return get_session()


@pytest.fixture(autouse=True)
def clean_tables(db_session):
    from api.app.models import Operator, RegistrationToken, Task, Agent

    db_session.query(Task).delete()
    db_session.query(Agent).delete()
    db_session.query(RegistrationToken).delete()
    db_session.query(Operator).delete()
    db_session.commit()
    yield