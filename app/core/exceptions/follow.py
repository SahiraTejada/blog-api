"""
Follow Exceptions Module

This module provides exceptions specific to Follow operations
such as follow/unfollow and relationship validation.
"""

from app.core.error_codes import ErrorCode
from app.core.exceptions.common import BadRequestException, ConflictException, NotFoundException


class FollowNotFoundException(NotFoundException):
    """
    Follow relationship not found exception.

    Use when trying to unfollow a user that is not being followed.
    """

    code = ErrorCode.NOT_FOUND
    message = "Follow relationship not found"

    def __init__(self) -> None:
        """Initialize follow not found exception."""
        super().__init__(resource="Follow relationship")


class AlreadyFollowingException(ConflictException):
    """
    Already following exception.

    Use when a user tries to follow someone they already follow.
    """

    message = "You are already following this user"
    code = ErrorCode.ALREADY_EXISTS


class CannotFollowSelfException(BadRequestException):
    """
    Cannot follow self exception.

    Use when a user tries to follow themselves.
    """

    message = "You cannot follow yourself"
    code = ErrorCode.BAD_REQUEST
