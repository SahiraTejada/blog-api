"""
Common Exceptions Module

This module provides common exceptions used across the application
such as not found, conflict, validation, and permission errors.
"""

from typing import Any, Dict, Optional

from app.core.error_codes import ErrorCode
from app.core.exceptions.base import AppException


class NotFoundException(AppException):
    """
    Resource not found exception (404).

    Use when a requested resource does not exist in the database.

    Example:
        raise NotFoundException(resource="User", identifier="123")
    """

    message = "Resource not found"
    code = ErrorCode.NOT_FOUND
    status_code = 404

    def __init__(
        self,
        resource: str = "Resource",
        identifier: Optional[str] = None,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize not found exception.

        Args:
            resource: Name of the resource (e.g., "User", "Post")
            identifier: Resource identifier (e.g., UUID)
            message: Custom message (overrides default)
            details: Additional error details
        """
        if message is None:
            if identifier:
                message = f"{resource} with id '{identifier}' not found"
            else:
                message = f"{resource} not found"
        super().__init__(message=message, details=details)


class ConflictException(AppException):
    """
    Conflict exception (409).

    Use when a resource already exists or there's a constraint violation.

    Example:
        raise ConflictException(message="Email already registered")
    """

    message = "Resource already exists"
    code = ErrorCode.CONFLICT
    status_code = 409


class ValidationException(AppException):
    """
    Validation error exception (422).

    Use when input validation fails beyond Pydantic's automatic validation.

    Example:
        raise ValidationException(
            message="Password too weak",
            details={"field": "password", "reason": "Must contain uppercase"}
        )
    """

    message = "Validation error"
    code = ErrorCode.VALIDATION_ERROR
    status_code = 422


class ForbiddenException(AppException):
    """
    Forbidden access exception (403).

    Use when user is authenticated but lacks permission.

    Example:
        raise ForbiddenException(message="Only admins can perform this action")
    """

    message = "Access forbidden"
    code = ErrorCode.FORBIDDEN
    status_code = 403


class BadRequestException(AppException):
    """
    Bad request exception (400).

    Use for malformed requests or invalid parameters.

    Example:
        raise BadRequestException(message="Invalid date format")
    """

    message = "Bad request"
    code = ErrorCode.BAD_REQUEST
    status_code = 400


class RateLimitException(AppException):
    """
    Rate limit exceeded exception (429).

    Use when user has exceeded request rate limits.

    Example:
        raise RateLimitException(message="Too many requests, try again later")
    """

    message = "Rate limit exceeded"
    code = ErrorCode.RATE_LIMIT_EXCEEDED
    status_code = 429
