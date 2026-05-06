from flask import Blueprint, jsonify, request

from api.app.services.operator_service import (
    register_operator,
    login_operator,
)

operator_auth_bp = Blueprint("operator_auth", __name__)


@operator_auth_bp.post("/register")
def register_operator_route():
    data = request.get_json() or {}

    result, error = register_operator(
        registration_token=data.get("registration_token"),
        username=data.get("username"),
        password=data.get("password"),
    )

    if error:
        message, status_code = error
        return jsonify({"error": message}), status_code

    return jsonify({"data": result}), 201


@operator_auth_bp.post("/login")
def login_operator_route():
    data = request.get_json() or {}

    result, error = login_operator(
        username=data.get("username"),
        password=data.get("password"),
    )

    if error:
        message, status_code = error
        return jsonify({"error": message}), status_code

    return jsonify({"data": result}), 200