from flask import Flask, jsonify
from api.app.api.v1.health import health_bp

def create_app():
    app = Flask(__name__)

    @app.get("/")
    def home():
        return jsonify({
            "name": "Conquest API",
            "status": "running",
        }), 200

    app.register_blueprint(health_bp)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)