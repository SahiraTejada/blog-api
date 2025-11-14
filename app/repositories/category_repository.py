from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Category, Post
from app.repositories.base_repository import BaseRepository
from app.schemas.base import  PaginationParams


class CategoryRepository(BaseRepository[Category]):
    """
    Repository for Category model operations.

    Inherits common CRUD operations from BaseRepository and adds
    category-specific business logic.
    """

    def __init__(self, db: Session):
        """Initialize CategoryRepository with Category model."""
        super().__init__(Category, db)

    # ========================================================================
    # CATEGORY-SPECIFIC READ METHODS
    # ========================================================================

    def get_by_name(
        self,
        name: str,
        include_deleted: bool = False
    ) -> Optional[Category]:
        """
        Get a category by its name (case-insensitive).

        Args:
            name: The name of the category to find
            include_deleted: If True, includes soft-deleted categories

        Returns:
            The category instance if found, None otherwise

        Example:
            category = category_repo.get_by_name("Technology")
        """

        return self.get_by_text_field({"name": name}, include_deleted=include_deleted)

    def get_categories_with_post_count(
        self,
        include_deleted: bool = False
    ) -> List[Tuple[Category, int]]:
        """
        Get all categories with their associated post counts.

        Args:
            include_deleted: If True, includes soft-deleted categories

        Returns:
            List of tuples (category, post_count) for all categories

        Example:
            categories_with_counts = category_repo.get_categories_with_post_count()
            for category, count in categories_with_counts:
                print(f"{category.name}: {count} posts")
        """
        query = self.db.query(
            self.model,
            func.count(Post.uuid).label('post_count')
        ).outerjoin(
            self.model.posts
        ).group_by(self.model.uuid)

        if not include_deleted:
            query = query.filter(self.model.deleted_at.is_(None))

        results = query.all()
        return [(category, count) for category, count in results]

    def get_popular_categories(
        self,
        limit: Optional[int] = None,
        include_deleted: bool = False
    ) -> List[Category]:
        """
        Get categories ordered by post count (most popular first).

        Args:
            limit: Optional maximum number of categories to return
            include_deleted: If True, includes soft-deleted categories

        Returns:
            List of category instances ordered by popularity

        Example:
            # Get top 10 most popular categories
            top_categories = category_repo.get_popular_categories(limit=10)
        """
        query = self.db.query(
            self.model
        ).outerjoin(
            self.model.posts
        ).group_by(
            self.model.uuid
        ).order_by(
            func.count(Post.uuid).desc()
        )

        if not include_deleted:
            query = query.filter(self.model.deleted_at.is_(None))

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_all_categories(self,
                           include_deleted: bool = False,
                           search_term: Optional[str] = None,
                           pagination: Optional[PaginationParams] = None,
                           ) -> List[Category]:
        """
        Get all active (non-deleted) categories ordered by name.

        Uses get_multi() from BaseRepository.

        Returns:
            List of all active category instances ordered by name

        Example:
            categories = category_repo.get_active_categories()
        """
        search_fields = ["name", "description"] if search_term else None

        return self.get_multi(
            include_deleted=include_deleted,
            order_by="name",
            search_fields=search_fields,
            search_term=search_term,
            pagination=pagination,
            order_desc=False
        )

    # ========================================================================
    # GET OR CREATE METHODS (use BaseRepository methods)
    # ========================================================================

    def get_or_create_by_name(
        self,
        name: str,
        defaults: Optional[dict] = None
    ) -> Tuple[Category, bool]:
        """
        Get a category by name or create it if it doesn't exist.

        Uses get_or_create() from BaseRepository.

        Args:
            name: The category name
            defaults: Additional fields to set when creating (optional)

        Returns:
            Tuple of (category_instance, created)

        Example:
            category, created = category_repo.get_or_create_by_name(
                name="Technology",
                defaults={"description": "Tech-related posts"}
            )
        """
        return self.get_or_create(
            name=name,
            defaults=defaults
        )

    def bulk_create_categories(
        self,
        names: List[str]
    ) -> List[Category]:
        """
        Create multiple categories from a list of names.

        Skips categories that already exist.

        Args:
            names: List of category names to create

        Returns:
            List of newly created category instances

        Example:
            new_categories = category_repo.bulk_create_categories([
                "Technology", "Programming", "Design"
            ])
        """
        categories_to_create = []

        for name in names:
            existing = self.get_by_name(name)
            if not existing:
                categories_to_create.append({"name": name})

        if categories_to_create:
            # Uses create_multi() from BaseRepository
            return self.create_multi(categories_to_create)

        return []

    # ========================================================================
    # CATEGORY-SPECIFIC UPDATE METHODS
    # ========================================================================

    def update_category_name(
        self,
        category_uuid: UUID,
        new_name: str,
    ) -> Optional[Category]:
        """
        Update a category's name.

        Uses update() from BaseRepository.

        Args:
            category_uuid: UUID of the category to update
            new_name: The new name for the category

        Returns:
            Updated category instance, or None if not found

        Example:
            updated = category_repo.update_category_name(
                category_uuid=uuid_obj,
                new_name="New Technology"
            )
        """
        return self.update(category_uuid, {"name": new_name})

    # ========================================================================
    # VALIDATION METHODS
    # ========================================================================

    def name_exists(
        self,
        name: str,
        exclude_uuid: Optional[UUID] = None
    ) -> bool:
        """
        Check if a category name already exists (case-insensitive).

        Args:
            name: The name to check
            exclude_uuid: Optional UUID to exclude from check (for updates)

        Returns:
            True if the name exists, False otherwise

        Example:
            if category_repo.name_exists("Technology"):
                raise HTTPException(409, "Category already exists")
        """
        query = self.db.query(self.model.uuid).filter(
            func.lower(self.model.name) == name.lower()
        ).filter(self.model.deleted_at.is_(None))

        if exclude_uuid:
            query = query.filter(self.model.uuid != exclude_uuid)

        return query.first() is not None

    # ========================================================================
    # CATEGORY STATISTICS
    # ========================================================================

    def get_category_post_count(
        self,
        category_uuid: UUID
    ) -> int:
        """
        Get the number of posts in a specific category.

        Args:
            category_uuid: UUID of the category

        Returns:
            Number of posts in the category

        Example:
            count = category_repo.get_category_post_count(category_uuid)
        """
        category = self.get(category_uuid)
        if not category:
            return 0

        return self.db.query(Post).join(
            Post.categories
        ).filter(
            Category.uuid == category_uuid
        ).filter(
            Post.deleted_at.is_(None)
        ).count()

    def get_empty_categories(self) -> List[Category]:
        """
        Get all categories that have no posts.

        Returns:
            List of categories with zero posts

        Example:
            empty = category_repo.get_empty_categories()
        """
        query = self.db.query(
            self.model
        ).outerjoin(
            self.model.posts
        ).group_by(
            self.model.uuid
        ).having(
            func.count(Post.uuid) == 0
        ).filter(
            self.model.deleted_at.is_(None)
        )

        return query.all()
