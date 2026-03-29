"""
Comment Exceptions Module

This module provides exceptions specific to Comment operations
such as creation, retrieval, and validation.
"""

from typing import Optional

from app.core.error_codes import ErrorCode
from app.core.exceptions.common import BadRequestException, NotFoundException


class CommentNotFoundException(NotFoundException):
    """
    Comment not found exception.

    Example:
        raise CommentNotFoundException(identifier="123e4567-...")
    """

    code = ErrorCode.COMMENT_NOT_FOUND

    def __init__(self, identifier: Optional[str] = None):
        """
        Initialize Comment not found exception.

        Args:
            identifier: Comment UUID or identifier
        """
        super().__init__(resource="Comment", identifier=identifier)


class ParentCommentNotFoundException(NotFoundException):
    """
    Parent comment not found exception.

    Use when a reply references a parent comment that does not exist.
    """

    code = ErrorCode.COMMENT_NOT_FOUND
    message = "Parent comment not found"

    def __init__(self, identifier: Optional[str] = None):
        """
        Initialize Parent comment not found exception.

        Args:
            identifier: Parent comment UUID or identifier
        """
        super().__init__(
            resource="Parent comment",
            identifier=identifier,
        )


class CommentPostMismatchException(BadRequestException):
    """
    Parent comment does not belong to the specified post.

    Use when a reply references a parent comment from a different post.
    """

    message = "Parent comment does not belong to this post"
    code = ErrorCode.BAD_REQUEST
