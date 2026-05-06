import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(BASE_DIR, "conquest.sqlite3")

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me-increasing-due-to-length-requirements")