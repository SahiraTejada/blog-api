"""
Category Service Module

This module provides category management business logic including
category creation, retrieval, updates, deletion, and statistics.

Architecture Flow:
    Route → CategoryService → CategoryRepository → Database

The CategoryService handles:
    - Category creation (single and bulk)
    - Category retrieval by UUID or name
    - Category listing with search and pagination
    - Category updates with name uniqueness validation
    - Category deletion (soft delete)
    - Category statistics (post counts, popular categories)
    - Get or create operations
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions.category import (
    CategoryNameExistsException,
    CategoryNotFoundException,
)
from app.models.categories import Category
from app.repositories.category_repository import CategoryRepository
from app.schemas.base import PaginationParams
from app.services.base_service import BaseService

if TYPE_CHECKING:
    from app.schemas.base import PaginatedResponse


class CategoryService(BaseService[Category]):
    """
    Service for category management operations.

    This service handles category creation, retrieval, updates, and deletion.

    Attributes:
        category_repo: CategoryRepository instance for database operations

    Example:
        category_service = CategoryService(db)
        category = category_service.create_category(
            name="Technology",
            description="Posts about technology"
        )
    """

    def __init__(self, db: Session):
        """
        Initialize CategoryService with database session.

        Args:
            db: SQLAlchemy database session from FastAPI dependency

        Example:
            category_service = CategoryService(db)
        """
        self.category_repo = CategoryRepository(db)

        super().__init__(self.category_repo)

    # ========================================================================
    # CATEGORY CREATION
    # ========================================================================

    def create_category(
        self, name: str, description: Optional[str] = None
    ) -> Category:
        """
        Create a new category.

        Args:
            name: Unique category name
            description: Optional category description

        Returns:
            Category: The created category model instance

        Raises:
            CategoryNameExistsException: If category name already exists
        """
        if self.category_repo.name_exists(name):
            raise CategoryNameExistsException()

        category_data: Dict[str, Any] = {
            "name": name,
            "description": description,
        }

        return self.create(category_data)

    # ========================================================================
    # CATEGORY RETRIEVAL
    # ========================================================================

    def get_by_category_uuid(self, category_uuid: UUID) -> Category:
        """
        Get category by UUID.

        Args:
            category_uuid: UUID of the category to retrieve

        Returns:
            Category: The category model instance

        Raises:
            CategoryNotFoundException: If category with given UUID does not exist
        """
        category = self.category_repo.get_by_uuid(category_uuid)

        if not category:
            raise CategoryNotFoundException()

        return category

    def get_by_name(self, name: str) -> Category:
        """
        Get category by name.

        Args:
            name: The name of the category to retrieve

        Returns:
            Category: The category model instance

        Raises:
            CategoryNotFoundException: If category with given name does not exist
        """
        category = self.category_repo.get_by_name(name)

        if not category:
            raise CategoryNotFoundException()

        return category

    def get_all_categories(
        self,
        pagination: PaginationParams,
        search_term: Optional[str] = None,
    ) -> PaginatedResponse[Category]:
        """
        Get all active categories with optional search and pagination.

        Args:
            pagination: Pagination parameters (page, page_size)
            search_term: Search in category name and description

        Returns:
            PaginatedResponse with categories and pagination metadata
        """
        return self.category_repo.get_all_categories(
            search_term=search_term,
            pagination=pagination,
        )

    def get_categories_with_post_count(self) -> List[Tuple[Category, int]]:
        """
        Get all categories with their associated post counts.

        Returns:
            List of tuples (category, post_count)
        """
        return self.category_repo.get_categories_with_post_count()

    def get_popular_categories(self, limit: Optional[int] = None) -> List[Category]:
        """
        Get categories ordered by post count (most popular first).

        Args:
            limit: Optional maximum number of categories to return

        Returns:
            List of categories ordered by popularity
        """
        return self.category_repo.get_popular_categories(limit=limit)

    def get_empty_categories(self) -> List[Category]:
        """
        Get all categories that have no posts.

        Returns:
            List of categories with zero posts
        """
        return self.category_repo.get_empty_categories()

    # ========================================================================
    # CATEGORY STATISTICS
    # ========================================================================

    def get_category_post_count(self, category_uuid: UUID) -> int:
        """
        Get the number of posts in a specific category.

        Args:
            category_uuid: UUID of the category

        Returns:
            Number of posts in the category

        Raises:
            CategoryNotFoundException: If category does not exist
        """
        category = self.category_repo.get_by_uuid(category_uuid)

        if not category:
            raise CategoryNotFoundException()

        return self.category_repo.get_category_post_count(category_uuid)

    # ========================================================================
    # GET OR CREATE / BULK OPERATIONS
    # ========================================================================

    def get_or_create_by_name(
        self, name: str, description: Optional[str] = None
    ) -> Tuple[Category, bool]:
        """
        Get a category by name or create it if it doesn't exist.

        Args:
            name: The category name
            description: Optional description (used only when creating)

        Returns:
            Tuple of (category, created) where created is True if new
        """
        defaults = {"description": description} if description else None
        return self.category_repo.get_or_create_by_name(name, defaults=defaults)

    def bulk_create_categories(self, categories_data: List[Dict[str, Any]]) -> List[Category]:
        """
        Create multiple categories from a list of dicts.

        Skips categories that already exist.

        Args:
            categories_data: List of dicts with "name" (required) and
                "description" (optional) keys

        Returns:
            List of newly created categories
        """
        return self.category_repo.bulk_create_categories(categories_data)

    # ========================================================================
    # CATEGORY UPDATE
    # ========================================================================

    def update_category(self, category_uuid: UUID, update_data: Dict[str, Any]) -> Category:
        """
        Update category information.

        Args:
            category_uuid: UUID of the category to update
            update_data: Dictionary of fields to update (e.g., name, description)

        Returns:
            Category: The updated category model instance

        Raises:
            CategoryNotFoundException: If category with given UUID does not exist
            CategoryNameExistsException: If new name already exists
        """
        category = self.category_repo.get_by_uuid(category_uuid)

        if not category:
            raise CategoryNotFoundException()

        new_name = update_data.get("name")
        if new_name and new_name != category.name:
            if self.category_repo.name_exists(new_name, exclude_uuid=category_uuid):
                raise CategoryNameExistsException()

        updated_category = self.category_repo.update(category_uuid, update_data)

        if not updated_category:
            raise CategoryNotFoundException()

        return updated_category

    # ========================================================================
    # CATEGORY DELETION
    # ========================================================================

    def delete_category(self, category_uuid: UUID) -> None:
        """
        Soft-delete a category.

        Args:
            category_uuid: UUID of the category to delete

        Raises:
            CategoryNotFoundException: If category with given UUID does not exist
        """
        deleted = self.category_repo.delete(category_uuid)

        if not deleted:
            raise CategoryNotFoundException()
