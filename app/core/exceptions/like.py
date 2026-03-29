"""
Like Exceptions Module

This module provides exceptions specific to Like operations
such as like/unlike and duplicate prevention.
"""

from app.core.error_codes import ErrorCode
from app.core.exceptions.common import ConflictException, NotFoundException


class LikeNotFoundException(NotFoundException):
    """
    Like not found exception.

    Use when trying to unlike a post that is not liked.
    """

    code = ErrorCode.NOT_FOUND
    message = "Like not found"

    def __init__(self) -> None:
        """Initialize like not found exception."""
        super().__init__(resource="Like")


class AlreadyLikedException(ConflictException):
    """
    Already liked exception.

    Use when a user tries to like a post they already liked.
    """

    message = "You have already liked this post"
    code = ErrorCode.ALREADY_EXISTS
