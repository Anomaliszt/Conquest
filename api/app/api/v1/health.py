from flask import Blueprint, jsonify
from sqlalchemy import text

from api.app.db.database import engine

health_bp = Blueprint("health", __name__)

@health_bp.get("/healthz")
def healthz():
    """Health check endpoint to verify that the API is running."""
    return jsonify({"status": "ok"}), 200


@health_bp.get("/readyz")
def readyz():
    """Ready check endpoint to verify that the API is ready to serve requests."""
    checks = {}
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
        status = "ready"
        code = 200
    except Exception:
        checks["database"] = "error"
        status = "not_ready"
        code = 503
    return jsonify({"status": status, "checks": checks}), code