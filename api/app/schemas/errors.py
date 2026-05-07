"""Global error response schemas used across the API."""

from pydantic import BaseModel, Field
from typing import Optional


class APIError(Exception):
    """Base exception for API errors."""

    def __init__(self, code: str, message: str, status: int = 400):
        self.code = code
        self.message = message
        self.status = status
        super().__init__(message)


class ErrorResponse(BaseModel):
    """Generic error response schema for failed requests."""
    request_id: str = Field(..., description="Unique request identifier")
    error: "ErrorDetail" = Field(..., description="Error information")


class ErrorDetail(BaseModel):
    """Error detail object in error response."""
    code: str = Field(..., description="Error code (e.g., BAD_REQUEST, UNAUTHORIZED)")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[list["ValidationErrorDetail"]] = Field(None, description="Additional error details for validation errors")


class ValidationErrorDetail(BaseModel):
    """Validation error detail for field-level errors."""
    field: str = Field(..., description="Field that failed validation")
    reason: str = Field(..., description="Reason for validation failure")
    value: Optional[str] = Field(None, description="Rejected value (omitted for secrets)")