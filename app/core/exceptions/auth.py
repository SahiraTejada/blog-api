"""
Authentication Exceptions Module

This module provides exceptions related to authentication and authorization.
All authentication exceptions return 401 Unauthorized by default.
"""

from typing import Optional

from app.core.error_codes import ErrorCode
from app.core.exceptions.base import AppException


class AuthenticationException(AppException):
    """
    Base authentication exception (401).

    Parent class for all authentication-related exceptions.
    """

    message = "Authentication failed"
    code = ErrorCode.AUTH_ERROR
    status_code = 401


class InvalidCredentialsException(AuthenticationException):
    """
    Invalid credentials exception.

    Use when email/password combination is incorrect.
    Message is intentionally generic to prevent user enumeration.

    Example:
        raise InvalidCredentialsException()
    """

    message = "Invalid email or password"
    code = ErrorCode.INVALID_CREDENTIALS


class TokenExpiredException(AuthenticationException):
    """
    Token expired exception.

    Use when JWT token has passed its expiration time.

    Example:
        raise TokenExpiredException()
    """

    message = "Token has expired"
    code = ErrorCode.EXPIRED_TOKEN


class TokenInvalidException(AuthenticationException):
    """
    Invalid token exception.

    Use when JWT token is malformed or signature is invalid.

    Example:
        raise TokenInvalidException()
    """

    message = "Invalid token"
    code = ErrorCode.INVALID_TOKEN


class TokenRevokedException(AuthenticationException):
    """
    Token revoked exception.

    Use when token exists but has been revoked (logout).

    Example:
        raise TokenRevokedException()
    """

    message = "Token has been revoked"
    code = ErrorCode.TOKEN_REVOKED


class TokenNotFoundException(AuthenticationException):
    """
    Token not found exception.

    Use when token does not exist in database.

    Example:
        raise TokenNotFoundException()
    """

    message = "Token not found or has been revoked"
    code = ErrorCode.TOKEN_NOT_FOUND


class TokenMissingException(AuthenticationException):
    """
    Token missing exception.

    Use when authorization header is missing.

    Example:
        raise TokenMissingException()
    """

    message = "Authorization token is required"
    code = ErrorCode.MISSING_TOKEN


class InvalidTokenTypeException(AuthenticationException):
    """
    Invalid token type exception.

    Use when token type doesn't match expected type.

    Example:
        raise InvalidTokenTypeException(expected="access", received="refresh")
    """

    message = "Invalid token type"
    code = ErrorCode.INVALID_TOKEN_TYPE

    def __init__(
        self,
        expected: Optional[str] = None,
        received: Optional[str] = None
    ):
        """
        Initialize with expected and received token types.

        Args:
            expected: Expected token type
            received: Received token type
        """
        if expected and received:
            message = f"Invalid token type. Expected '{expected}', got '{received}'"
        elif expected:
            message = f"Invalid token type. Expected '{expected}'"
        else:
            message = self.message
        super().__init__(message=message)


class MaxSessionsExceededException(AppException):
    """
    Maximum sessions exceeded exception (429).

    Use when user has reached the maximum number of concurrent sessions.

    Example:
        raise MaxSessionsExceededException(max_sessions=5)
    """

    message = "Maximum number of sessions exceeded"
    code = ErrorCode.MAX_SESSIONS_EXCEEDED
    status_code = 429

    def __init__(self, max_sessions: Optional[int] = None):
        """
        Initialize with max sessions limit.

        Args:
            max_sessions: Maximum allowed sessions
        """
        if max_sessions:
            message = f"Maximum number of sessions ({max_sessions}) exceeded. Please logout from another device."
        else:
            message = self.message
        super().__init__(message=message)
