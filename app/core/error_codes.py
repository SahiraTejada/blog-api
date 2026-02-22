"""
Error Codes Module

This module defines standardized error codes for the API.
These codes help the frontend identify specific error types
and provide appropriate user feedback.

Usage:
    from app.core.error_codes import ErrorCode

    raise AppException(code=ErrorCode.USER_NOT_FOUND)
"""

from enum import Enum


class ErrorCode(str, Enum):
    """
    Standardized error codes for API responses.

    These codes provide machine-readable error identification
    that the frontend can use for handling specific error cases.
    """

    # ========================================================================
    # VALIDATION ERRORS (400, 422)
    # ========================================================================
    VALIDATION_ERROR = "VALIDATION_ERROR"
    REQUIRED_FIELD = "REQUIRED_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"
    INVALID_VALUE = "INVALID_VALUE"
    BAD_REQUEST = "BAD_REQUEST"

    # ========================================================================
    # AUTHENTICATION ERRORS (401)
    # ========================================================================
    AUTH_ERROR = "AUTH_ERROR"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    INVALID_TOKEN = "INVALID_TOKEN"
    EXPIRED_TOKEN = "EXPIRED_TOKEN"
    MISSING_TOKEN = "MISSING_TOKEN"
    TOKEN_REVOKED = "TOKEN_REVOKED"
    TOKEN_NOT_FOUND = "TOKEN_NOT_FOUND"
    INVALID_TOKEN_TYPE = "INVALID_TOKEN_TYPE"
    PASSWORD_INCORRECT = "PASSWORD_INCORRECT"

    # ========================================================================
    # AUTHORIZATION ERRORS (403)
    # ========================================================================
    FORBIDDEN = "FORBIDDEN"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    USER_INACTIVE = "USER_INACTIVE"

    # ========================================================================
    # RESOURCE ERRORS - NOT FOUND (404)
    # ========================================================================
    NOT_FOUND = "NOT_FOUND"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    POST_NOT_FOUND = "POST_NOT_FOUND"
    COMMENT_NOT_FOUND = "COMMENT_NOT_FOUND"
    CATEGORY_NOT_FOUND = "CATEGORY_NOT_FOUND"

    # ========================================================================
    # RESOURCE ERRORS - CONFLICT (409)
    # ========================================================================
    CONFLICT = "CONFLICT"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    DUPLICATE_ENTRY = "DUPLICATE_ENTRY"
    USERNAME_EXISTS = "USERNAME_EXISTS"
    EMAIL_EXISTS = "EMAIL_EXISTS"

    # ========================================================================
    # DATABASE ERRORS (500)
    # ========================================================================
    DATABASE_ERROR = "DATABASE_ERROR"
    INTEGRITY_ERROR = "INTEGRITY_ERROR"
    CONNECTION_ERROR = "CONNECTION_ERROR"

    # ========================================================================
    # SERVER ERRORS (500)
    # ========================================================================
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"

    # ========================================================================
    # RATE LIMITING (429)
    # ========================================================================
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    MAX_SESSIONS_EXCEEDED = "MAX_SESSIONS_EXCEEDED"
