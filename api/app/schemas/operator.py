"""Pydantic schemas for operator registration and login endpoints."""

from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime


class RegisterOperatorRequest(BaseModel):
    """Request schema for operator registration endpoint.
    
    Validates that:
    - registration_token: 32-4096 characters (one-time token provisioned outside API)
    - username: 3-100 characters, alphanumeric with dots/underscores/dashes
    - password: 12-4096 characters (strong password requirement)
    
    These validations happen automatically before the endpoint handler runs.
    If any constraint fails, a 400 error with detailed errors is returned.
    """
    registration_token: str = Field(
        ..., 
        min_length=32, 
        max_length=4096,
        description="One-time token provisioned outside this API. This API does not expose an endpoint that creates registration tokens."
    )
    username: str = Field(
        ..., 
        min_length=3, 
        max_length=100,
        pattern="^[A-Za-z0-9_.-]+$",
        description="Unique username for the operator (alphanumeric with dots, underscores, dashes)"
    )
    password: str = Field(
        ..., 
        min_length=12, 
        max_length=4096,
        description="Password for the operator account (minimum 12 characters)"
    )


class LoginOperatorRequest(BaseModel):
    """Request schema for operator login endpoint.
    
    Both fields are required for authentication. No additional validation
    rules are applied here - business logic validation (operator exists, password matches)
    happens in the service layer.
    """
    username: str = Field(
        ..., 
        min_length=3, 
        max_length=100,
        description="Operator username"
    )
    password: str = Field(
        ..., 
        min_length=12, 
        max_length=4096,
        description="Operator password"
    )


class Operator(BaseModel):
    """Operator entity returned in responses."""
    id: str = Field(..., description="Unique operator ID (format: operator_<random>)")
    username: str = Field(..., description="Operator username")
    status: Literal["active", "disabled"] = Field(..., description="Operator account status")
    created_at: str = Field(..., description="ISO timestamp of operator creation")


class RegisterOperatorResponse(BaseModel):
    """Response schema for successful operator registration (HTTP 201).
    
    Returns the newly created operator details wrapped in a 'data' field.
    The 'created_at' field follows ISO 8601 format with timezone information.
    """
    data: Operator = Field(..., description="Newly created operator object")


class LoginOperatorResponse(BaseModel):
    """Response schema for successful operator login (HTTP 200).
    
    Returns JWT token for subsequent authenticated requests.
    Token expires in 900 seconds (15 minutes) by default.
    Wrapped in a 'data' field per contract.
    """
    data: "LoginOperatorTokenData" = Field(..., description="Token and operator details")


class LoginOperatorTokenData(BaseModel):
    """Token data returned in login response."""
    operator_id: str = Field(..., description="Operator ID")
    operator_token: str = Field(..., description="JWT token for authentication")
    token_type: Literal["Bearer"] = Field(..., description="Type of token (Bearer)")
    expires_in: int = Field(..., description="Token expiration time in seconds")
