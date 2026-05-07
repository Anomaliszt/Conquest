from flask import Blueprint, request

from api.app.schemas.errors import APIError
from api.app.services.operator_service import (
    register_operator,
    login_operator,
)
from api.app.schemas import (
    RegisterOperatorRequest,
    LoginOperatorRequest,
    RegisterOperatorResponse,
    LoginOperatorResponse,
)

operator_auth_bp = Blueprint("operator_auth", __name__)


@operator_auth_bp.post("/register")
def register_operator_route():
    """Register a new operator using a registration token.
    
    HTTP Responses:
    - 201: Operator successfully created
    - 400: Validation error or malformed request
    - 401: Invalid/expired/used registration token
    - 409: Username already exists
    """
    data = RegisterOperatorRequest(**request.get_json())

    result, error = register_operator(
        registration_token=data.registration_token,
        username=data.username,
        password=data.password,
    )

    if error:
        message, status_code = error
        raise APIError(
            code={401: "UNAUTHORIZED", 409: "CONFLICT"}.get(status_code, "INTERNAL_ERROR"),
            message=message,
            status=status_code
        )

    return RegisterOperatorResponse(data=result).model_dump(), 201


@operator_auth_bp.post("/login")
def login_operator_route():
    """Authenticate an operator and return JWT token.
    
    HTTP Responses:
    - 200: Login successful, token returned
    - 400: Validation error or malformed request
    - 401: Invalid credentials or account disabled
    """
    data = LoginOperatorRequest(**request.get_json())

    result, error = login_operator(
        username=data.username,
        password=data.password,
    )

    if error:
        message, status_code = error
        raise APIError(
            code="UNAUTHORIZED" if status_code == 401 else "INTERNAL_ERROR",
            message=message,
            status=status_code
        )

    return LoginOperatorResponse(data=result).model_dump(), 200