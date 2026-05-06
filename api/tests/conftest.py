import os
import sqlite3
import sys
from pathlib import Path

import pytest

API_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = API_DIR.parent

sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture()
def temp_database(tmp_path, monkeypatch):
    db_path = tmp_path / "test_conquest.sqlite3"
    schema_path = API_DIR / "app" / "db" / "schema.sql"

    conn = sqlite3.connect(db_path)
    with open(schema_path, "r", encoding="utf-8") as schema_file:
        conn.executescript(schema_file.read())
    conn.commit()
    conn.close()

    monkeypatch.setattr("api.app.db.sqlite.DATABASE_PATH", str(db_path))

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
def db_connection(temp_database):
    conn = sqlite3.connect(temp_database)
    conn.row_factory = sqlite3.Row

    try:
        yield conn
    finally:
        conn.close()