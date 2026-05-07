from flask import jsonify, g
from pydantic import ValidationError

from api.app.schemas.errors import ErrorResponse, ErrorDetail, ValidationErrorDetail, APIError


def register_error_handlers(app):
    @app.errorhandler(Exception)
    def handle_error(e):
        request_id = getattr(g, 'request_id', "")

        if isinstance(e, ValidationError):
            response = ErrorResponse(
                request_id=request_id,
                error=ErrorDetail(
                    code="BAD_REQUEST",
                    message="Invalid request payload",
                    details=[
                        ValidationErrorDetail(
                            field=".".join(map(str, err["loc"])),
                            reason=err["msg"],
                            value=str(err["input"]) if "input" in err else None
                        )
                        for err in e.errors()
                    ]
                )
            )
            return jsonify(response.model_dump()), 400

        if isinstance(e, APIError):
            response = ErrorResponse(
                request_id=request_id,
                error=ErrorDetail(code=e.code, message=e.message)
            )
            return jsonify(response.model_dump()), e.status

        response = ErrorResponse(
            request_id=request_id,
            error=ErrorDetail(code="INTERNAL_ERROR", message="An unexpected error occurred")
        )
        return jsonify(response.model_dump()), 500

    @app.before_request
    def store_request_id():
        import uuid
        g.request_id = str(uuid.uuid4())