import os
import sys
from pathlib import Path

import pytest

API_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = API_DIR.parent

sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture()
def temp_database(tmp_path, monkeypatch):
    db_path = tmp_path / "test_conquest.sqlite3"

    monkeypatch.setattr("api.app.config.DATABASE_PATH", str(db_path))

    from api.app.db.database import engine
    from api.app.models import Base
    Base.metadata.create_all(bind=engine)

    return db_path


@pytest.fixture()
def app(temp_database):
    from api.app.main import create_app

    app = create_app()
    app.config.update(TESTING=True)

    return app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db_session(temp_database):
    from api.app.db import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def clean_tables(db_session):
    from api.app.models import Operator, RegistrationToken, Task, Agent

    db_session.query(Task).delete()
    db_session.query(Agent).delete()
    db_session.query(RegistrationToken).delete()
    db_session.query(Operator).delete()
    db_session.commit()
    yield