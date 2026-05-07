import sqlite3
from api.app.config import DATABASE_PATH

def get_connection():
    """Creates and returns a new SQLite database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn