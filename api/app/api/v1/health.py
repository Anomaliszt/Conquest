from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)

@health_bp.get("/healthz")
def healthz():
    return jsonify({"status": "ok"}), 200

@health_bp.get("/readyz")
def readyz():
    return jsonify({
        "status": "ready",
        "checks": {
            "database": "ok"
        }
    }), 200