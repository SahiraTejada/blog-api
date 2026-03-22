"""
Post Exceptions Module

This module provides exceptions specific to Post operations
such as creation, updates, and lookups.

"""

from typing import Optional

from app.core.error_codes import ErrorCode
from app.core.exceptions.common import ConflictException, NotFoundException


class PostNotFoundException(NotFoundException):
    """
    Post not found exception.

    Example:
        raise PostNotFoundException(identifier="123e4567-...")
    """

    code = ErrorCode.POST_NOT_FOUND

    def __init__(self, identifier: Optional[str] = None):
        """
        Initialize Post not found exception.

        Args:
            identifier: Post UUID or identifier
        """
        super().__init__(resource="Post", identifier=identifier)


class PostNameExistsException(ConflictException):
    """
    Post name already exists exception.

    Use when creating or updating a Post with a duplicate name.

    Example:
        raise PostNameExistsException()
    """

    message = "Post name already exists"
    code = ErrorCode.ALREADY_EXISTS
