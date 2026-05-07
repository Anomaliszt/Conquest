from flask import Flask, jsonify
from api.app.api.v1.health import health_bp
from api.app.api.v1.operator_auth import operator_auth_bp
from api.app.exceptions import register_error_handlers


def create_app():
    app = Flask(__name__)
    register_error_handlers(app)

    @app.get("/")
    def home():
        return jsonify({
            "name": "Conquest API",
            "status": "running",
        }), 200

    app.register_blueprint(health_bp)
    app.register_blueprint(operator_auth_bp, url_prefix="/api/v1/operator")

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)