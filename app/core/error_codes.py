"""
Error Codes Module

This module defines standardized error codes for the API.
These codes help the frontend identify specific error types
and provide appropriate user feedback.
"""

from enum import Enum


class ErrorCode(str, Enum):
    """
    Standardized error codes for API responses.

    These codes provide machine-readable error identification
    that the frontend can use for handling specific error cases.
    """

    # Validation Errors (4xx)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    REQUIRED_FIELD = "REQUIRED_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"
    INVALID_VALUE = "INVALID_VALUE"

    # Authentication Errors (401)
    INVALID_TOKEN = "INVALID_TOKEN"
    EXPIRED_TOKEN = "EXPIRED_TOKEN"
    MISSING_TOKEN = "MISSING_TOKEN"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"

    # Authorization Errors (403)
    PERMISSION_DENIED = "PERMISSION_DENIED"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    FORBIDDEN = "FORBIDDEN"

    # Resource Errors (404, 409)
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    DUPLICATE_ENTRY = "DUPLICATE_ENTRY"
    CONFLICT = "CONFLICT"

    # Database Errors (500)
    DATABASE_ERROR = "DATABASE_ERROR"
    INTEGRITY_ERROR = "INTEGRITY_ERROR"
    CONNECTION_ERROR = "CONNECTION_ERROR"

    # Server Errors (500)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"

    # Rate Limiting (429)
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
