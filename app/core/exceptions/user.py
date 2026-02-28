"""
User Exceptions Module

This module provides exceptions specific to user operations
such as registration, profile updates, and user lookups.
"""

from typing import Optional

from app.core.error_codes import ErrorCode
from app.core.exceptions.base import AppException
from app.core.exceptions.common import ConflictException, NotFoundException


class UserNotFoundException(NotFoundException):
    """
    User not found exception.

    Example:
        raise UserNotFoundException(identifier="123e4567-...")
    """

    code = ErrorCode.USER_NOT_FOUND

    def __init__(self, identifier: Optional[str] = None):
        """
        Initialize user not found exception.

        Args:
            identifier: User UUID or identifier
        """
        super().__init__(resource="User", identifier=identifier)


class UsernameExistsException(ConflictException):
    """
    Username already exists exception.

    Use during registration when username is taken.

    Example:
        raise UsernameExistsException()
    """

    message = "Username already exists"
    code = ErrorCode.USERNAME_EXISTS


class EmailExistsException(ConflictException):
    """
    Email already registered exception.

    Use during registration when email is already in use.

    Example:
        raise EmailExistsException()
    """

    message = "Email already registered"
    code = ErrorCode.EMAIL_EXISTS


class PasswordIncorrectException(AppException):
    """
    Password incorrect exception.

    Use when current password verification fails (e.g., password change).

    Example:
        raise PasswordIncorrectException()
    """

    message = "Current password is incorrect"
    code = ErrorCode.PASSWORD_INCORRECT
    status_code = 401


class UserInactiveException(AppException):
    """
    User inactive exception.

    Use when user account is deactivated or suspended.

    Example:
        raise UserInactiveException()
    """

    message = "User account is inactive"
    code = ErrorCode.USER_INACTIVE
    status_code = 403
