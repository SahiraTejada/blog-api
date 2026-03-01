"""
Category Exceptions Module

This module provides exceptions specific to category operations
such as creation, updates, and lookups.

"""

from typing import Optional

from app.core.error_codes import ErrorCode
from app.core.exceptions.common import ConflictException, NotFoundException


class CategoryNotFoundException(NotFoundException):
    """
    Category not found exception.

    Example:
        raise CategoryNotFoundException(identifier="123e4567-...")
    """

    code = ErrorCode.CATEGORY_NOT_FOUND

    def __init__(self, identifier: Optional[str] = None):
        """
        Initialize category not found exception.

        Args:
            identifier: Category UUID or identifier
        """
        super().__init__(resource="Category", identifier=identifier)


class CategoryNameExistsException(ConflictException):
    """
    Category name already exists exception.

    Use when creating or updating a category with a duplicate name.

    Example:
        raise CategoryNameExistsException()
    """

    message = "Category name already exists"
    code = ErrorCode.ALREADY_EXISTS
