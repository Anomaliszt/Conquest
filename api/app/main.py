"""Flask application factory for the Conquest API."""

import os
from flask import Flask, jsonify
from api.app.api.v1.health import health_bp
from api.app.api.v1.operator_auth import operator_auth_bp
from api.app.api.v1.agent_auth import agent_auth_bp
from api.app.api.v1.agents import agents_bp
from api.app.api.v1.tasks import tasks_bp
from api.app.exceptions import register_error_handlers
from api.app.db import init_db
from api.app.ws import socketio, init_socketio, register_handlers


def create_app(testing=False):
    """Create and configure the Flask application instance.

    Initializes error handlers, database connection, and registers
    all API blueprints with their respective URL prefixes.
    """
    app = Flask(__name__)
    app.config['TESTING'] = testing
    register_error_handlers(app)
    init_db()

    init_socketio(app)
    register_handlers()

    if not testing:
        from api.app.ws.deadlines import start_deadline_checker
        start_deadline_checker()

    @app.get("/")
    def home():
        return jsonify({
            "name": "Conquest API",
            "status": "running",
        }), 200

    app.register_blueprint(health_bp)
    app.register_blueprint(operator_auth_bp, url_prefix="/api/v1/operator")
    app.register_blueprint(agent_auth_bp, url_prefix="/api/v1/agent")
    app.register_blueprint(agents_bp, url_prefix="/api/v1/agents")
    app.register_blueprint(tasks_bp)

    return app

app = create_app(testing=os.environ.get('FLASK_TESTING', '').lower() == 'true')

if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", port=8000, debug=True)