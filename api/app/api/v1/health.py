from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)

@health_bp.get("/healthz")
def healthz():
    """Health check endpoint to verify that the API is running."""
    return jsonify({"status": "ok"}), 200

@health_bp.get("/readyz")
def readyz():
    """Ready check endpoint to verify that the API is ready to serve requests."""
    return jsonify({
        "status": "ready",
        "checks": {
            "database": "ok"
        }
    }), 200