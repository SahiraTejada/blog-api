"""
Custom Application Exceptions

This module exports all custom exceptions for the application.
Import exceptions from here rather than individual modules.

Usage:
    from app.core.exceptions import (
        UserNotFoundException,
        InvalidCredentialsException,
        EmailExistsException,
    )

All exceptions inherit from AppException and include:
    - message: Human-readable error message
    - code: ErrorCode enum value for frontend handling
    - status_code: HTTP status code
    - details: Optional additional information
"""

from app.core.exceptions.base import AppException
from app.core.exceptions.common import (
    NotFoundException,
    ConflictException,
    ValidationException,
    ForbiddenException,
    BadRequestException,
    RateLimitException,
)
from app.core.exceptions.auth import (
    AuthenticationException,
    InvalidCredentialsException,
    TokenExpiredException,
    TokenInvalidException,
    TokenRevokedException,
    TokenNotFoundException,
    TokenMissingException,
    InvalidTokenTypeException,
    MaxSessionsExceededException,
)
from app.core.exceptions.user import (
    UserNotFoundException,
    UsernameExistsException,
    EmailExistsException,
    PasswordIncorrectException,
    UserInactiveException,
)

__all__ = [
    # Base
    "AppException",
    # Common
    "NotFoundException",
    "ConflictException",
    "ValidationException",
    "ForbiddenException",
    "BadRequestException",
    "RateLimitException",
    # Auth
    "AuthenticationException",
    "InvalidCredentialsException",
    "TokenExpiredException",
    "TokenInvalidException",
    "TokenRevokedException",
    "TokenNotFoundException",
    "TokenMissingException",
    "InvalidTokenTypeException",
    "MaxSessionsExceededException",
    # User
    "UserNotFoundException",
    "UsernameExistsException",
    "EmailExistsException",
    "PasswordIncorrectException",
    "UserInactiveException",
]
