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

from app.core.exceptions.auth import (
    AuthenticationException,
    InvalidCredentialsException,
    InvalidTokenTypeException,
    MaxSessionsExceededException,
    TokenExpiredException,
    TokenInvalidException,
    TokenMissingException,
    TokenNotFoundException,
    TokenRevokedException,
)
from app.core.exceptions.base import AppException
from app.core.exceptions.common import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    RateLimitException,
    ValidationException,
)
from app.core.exceptions.category import (
    CategoryNameExistsException,
    CategoryNotFoundException,
)
from app.core.exceptions.user import (
    EmailExistsException,
    PasswordIncorrectException,
    UserInactiveException,
    UsernameExistsException,
    UserNotFoundException,
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
    # Category
    "CategoryNotFoundException",
    "CategoryNameExistsException",
    # User
    "UserNotFoundException",
    "UsernameExistsException",
    "EmailExistsException",
    "PasswordIncorrectException",
    "UserInactiveException",
]
