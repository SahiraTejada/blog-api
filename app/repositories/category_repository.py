"""
Category Repository Module

This module provides data access methods specific to the Category model.
It extends the BaseRepository with category-specific operations.

This serves as an example of how to create domain-specific repositories
that inherit from the BaseRepository class.

Author: Blog API Team
Date: 2025-10-20
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.base import BaseModel
from app.repositories.base_repository import BaseRepository


# ============================================================================
# CATEGORY REPOSITORY CLASS
# ============================================================================

class CategoryRepository(BaseRepository[BaseModel]):
    """
    Repository for Category-specific database operations.

    This class extends BaseRepository to provide category-specific methods
    while inheriting all the standard CRUD operations.

    The pattern is:
    1. Inherit from BaseRepository[YourModel]
    2. Pass the model class in __init__
    3. Add domain-specific methods as needed

    Example Usage:
        # Initialize the repository
        category_repo = CategoryRepository(db_session)

        # Use inherited methods from BaseRepository
        category = category_repo.get(category_uuid)
        all_categories = category_repo.get_all()

        # Use category-specific methods
        tech_category = category_repo.get_by_name("Technology")
        popular_categories = category_repo.get_popular_categories(limit=5)
    """

    def __init__(self, db: Session):
        """
        Initialize the Category repository.

        Args:
            db: SQLAlchemy database session

        Note:
            We don't need to import the Category model here yet since
            it's not implemented. This is a placeholder showing the pattern.
            When your Category model is ready, you'll pass it to super().__init__()
            like this: super().__init__(Category, db)
        """
        # TODO: Replace BaseModel with actual Category model when implemented
        # from app.models.category import Category
        # super().__init__(Category, db)
        super().__init__(BaseModel, db)

    # ========================================================================
    # CATEGORY-SPECIFIC QUERY METHODS
    # ========================================================================

    def get_by_name(self, name: str, include_deleted: bool = False) -> Optional[BaseModel]:
        """
        Get a category by its name (case-insensitive).

        This is a common operation for categories since they're often
        referenced by name in APIs.

        Args:
            name: The name of the category to find
            include_deleted: If True, includes soft-deleted categories

        Returns:
            The category instance if found, None otherwise

        Example:
            tech_category = category_repo.get_by_name("Technology")
            if tech_category:
                print(f"Found category: {tech_category.uuid}")
        """
        query = self.db.query(self.model).filter(
            func.lower(self.model.name) == name.lower()
        )

        if not include_deleted:
            query = query.filter(self.model.deleted_at.is_(None))

        return query.first()

    def get_by_slug(self, slug: str, include_deleted: bool = False) -> Optional[BaseModel]:
        """
        Get a category by its URL slug.

        Slugs are URL-friendly versions of names (e.g., "web-development"
        instead of "Web Development"). They're commonly used in REST APIs
        for cleaner URLs.

        Args:
            slug: The URL slug of the category
            include_deleted: If True, includes soft-deleted categories

        Returns:
            The category instance if found, None otherwise

        Example:
            category = category_repo.get_by_slug("web-development")
        """
        query = self.db.query(self.model).filter(self.model.slug == slug)

        if not include_deleted:
            query = query.filter(self.model.deleted_at.is_(None))

        return query.first()

    def get_popular_categories(
        self,
        limit: int = 10,
        include_deleted: bool = False
    ) -> List[BaseModel]:
        """
        Get the most popular categories based on post count.

        This assumes your Category model has a relationship with Posts.
        It's useful for displaying trending or featured categories.

        Args:
            limit: Maximum number of categories to return
            include_deleted: If True, includes soft-deleted categories

        Returns:
            List of category instances ordered by popularity

        Example:
            # Get top 5 popular categories for homepage
            popular = category_repo.get_popular_categories(limit=5)

        Note:
            This is a placeholder implementation. When your Category model
            has the posts relationship, you'll use:
            .join(Post).group_by(Category.uuid).order_by(func.count(Post.uuid).desc())
        """
        query = self.db.query(self.model)

        if not include_deleted:
            query = query.filter(self.model.deleted_at.is_(None))

        # TODO: Add actual post count ordering when Post model is implemented
        # For now, just return by created_at
        return query.order_by(self.model.created_at.desc()).limit(limit).all()

    def search_categories(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[BaseModel]:
        """
        Search categories by name or description.

        This uses the inherited search() method from BaseRepository but
        provides a more specific interface for categories.

        Args:
            search_term: Text to search for
            skip: Number of records to skip (pagination)
            limit: Maximum number of results

        Returns:
            List of matching category instances

        Example:
            # Search for categories related to "web"
            results = category_repo.search_categories("web", limit=10)
        """
        # Use the inherited search method with category-specific fields
        return self.search(
            search_fields=["name", "description"],
            search_term=search_term,
            skip=skip,
            limit=limit
        )

    def get_or_create_by_name(self, name: str, **kwargs) -> tuple[BaseModel, bool]:
        """
        Get a category by name or create it if it doesn't exist.

        This is particularly useful for importing content or handling
        API requests where categories might be specified by name.

        Args:
            name: The category name
            **kwargs: Additional fields to set when creating (e.g., description)

        Returns:
            Tuple of (category_instance, created) where created is True
            if a new category was created

        Example:
            # Ensure a category exists
            category, created = category_repo.get_or_create_by_name(
                name="Technology",
                description="Tech related posts",
                slug="technology"
            )
            if created:
                print("Created new category")
        """
        # Try to find existing category
        existing = self.get_by_name(name)

        if existing:
            return existing, False

        # Create new category
        obj_in = {"name": name, **kwargs}
        new_category = self.create(obj_in)
        return new_category, True

    def get_active_categories(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[BaseModel]:
        """
        Get all active (non-deleted) categories with optional filtering.

        This is a convenience method that's clearer than calling get_multi()
        for the common use case of fetching active categories.

        Args:
            skip: Number of records to skip (pagination)
            limit: Maximum number of categories to return

        Returns:
            List of active category instances

        Example:
            # Get first page of categories (20 per page)
            categories = category_repo.get_active_categories(skip=0, limit=20)

            # Get second page
            categories = category_repo.get_active_categories(skip=20, limit=20)
        """
        return self.get_multi(
            skip=skip,
            limit=limit,
            include_deleted=False,
            order_by="name",
            order_desc=False
        )

    def get_categories_with_post_count(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[tuple[BaseModel, int]]:
        """
        Get categories with their associated post counts.

        This is useful for displaying category lists with statistics,
        such as "Technology (25 posts)".

        Args:
            skip: Number of records to skip (pagination)
            limit: Maximum number of categories to return

        Returns:
            List of tuples (category, post_count)

        Example:
            categories_with_counts = category_repo.get_categories_with_post_count()
            for category, count in categories_with_counts:
                print(f"{category.name}: {count} posts")

        Note:
            This is a placeholder. When Post model is implemented, you'll use:
            .outerjoin(Post).group_by(Category).with_entities(Category, func.count(Post.uuid))
        """
        # TODO: Implement actual post counting when Post model exists
        # For now, return categories with zero count
        categories = self.get_multi(
            skip=skip,
            limit=limit,
            include_deleted=False
        )
        return [(cat, 0) for cat in categories]

    def bulk_create_categories(self, names: List[str]) -> List[BaseModel]:
        """
        Create multiple categories from a list of names.

        This is useful for initial data seeding or bulk imports.

        Args:
            names: List of category names to create

        Returns:
            List of created category instances

        Example:
            # Create default categories
            default_categories = [
                "Technology", "Sports", "Politics",
                "Entertainment", "Science", "Health"
            ]
            created = category_repo.bulk_create_categories(default_categories)
            print(f"Created {len(created)} categories")

        Note:
            This skips categories that already exist to avoid duplicates.
        """
        categories_to_create = []

        for name in names:
            # Check if category already exists
            existing = self.get_by_name(name)
            if not existing:
                # TODO: Add slug generation when Category model is complete
                categories_to_create.append({
                    "name": name,
                    # "slug": generate_slug(name),  # Implement slug generation
                })

        # Use inherited create_multi method
        if categories_to_create:
            return self.create_multi(categories_to_create)

        return []

    # ========================================================================
    # CATEGORY-SPECIFIC UPDATE METHODS
    # ========================================================================

    def update_category_name(
        self,
        category_id: UUID,
        new_name: str,
        update_slug: bool = True
    ) -> Optional[BaseModel]:
        """
        Update a category's name and optionally regenerate its slug.

        Args:
            category_id: UUID of the category to update
            new_name: The new name for the category
            update_slug: If True, regenerates the slug from the new name

        Returns:
            Updated category instance, or None if not found

        Example:
            updated = category_repo.update_category_name(
                category_id=cat_uuid,
                new_name="Web Development"
            )
        """
        update_data = {"name": new_name}

        # TODO: Add slug generation when Category model is complete
        # if update_slug:
        #     update_data["slug"] = generate_slug(new_name)

        return self.update(category_id, update_data)

    # ========================================================================
    # VALIDATION METHODS
    # ========================================================================

    def name_exists(self, name: str, exclude_id: Optional[UUID] = None) -> bool:
        """
        Check if a category name already exists.

        Useful for validation before creating or updating categories.

        Args:
            name: The name to check
            exclude_id: Optional UUID to exclude from check (for updates)

        Returns:
            True if the name exists, False otherwise

        Example:
            # Check before creating
            if category_repo.name_exists("Technology"):
                print("Category name already taken")

            # Check before updating (exclude current category)
            if category_repo.name_exists("Technology", exclude_id=current_cat_id):
                print("Another category already has this name")
        """
        query = self.db.query(self.model.uuid).filter(
            func.lower(self.model.name) == name.lower()
        ).filter(self.model.deleted_at.is_(None))

        if exclude_id:
            query = query.filter(self.model.uuid != exclude_id)

        return query.first() is not None

    def __repr__(self) -> str:
        """
        String representation of the category repository.

        Returns:
            A string describing this repository instance
        """
        return f"<CategoryRepository(model={self.model.__name__})>"


# ============================================================================
# USAGE EXAMPLES AND PATTERNS
# ============================================================================
"""
EXAMPLE USAGE IN FASTAPI ROUTES:

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.repositories.category_repository import CategoryRepository

router = APIRouter()

@router.get("/categories")
def get_categories(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    # Initialize repository
    category_repo = CategoryRepository(db)

    # Get categories
    categories = category_repo.get_active_categories(skip=skip, limit=limit)

    return categories


@router.get("/categories/{category_id}")
def get_category(
    category_id: UUID,
    db: Session = Depends(get_db)
):
    category_repo = CategoryRepository(db)
    category = category_repo.get(category_id)

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    return category


@router.post("/categories")
def create_category(
    name: str,
    description: str,
    db: Session = Depends(get_db)
):
    category_repo = CategoryRepository(db)

    # Validate name doesn't exist
    if category_repo.name_exists(name):
        raise HTTPException(status_code=400, detail="Category name already exists")

    # Create category
    category = category_repo.create({
        "name": name,
        "description": description
    })

    return category


@router.put("/categories/{category_id}")
def update_category(
    category_id: UUID,
    name: str,
    db: Session = Depends(get_db)
):
    category_repo = CategoryRepository(db)

    # Validate name doesn't exist for other categories
    if category_repo.name_exists(name, exclude_id=category_id):
        raise HTTPException(status_code=400, detail="Category name already exists")

    # Update category
    updated = category_repo.update_category_name(category_id, name)

    if not updated:
        raise HTTPException(status_code=404, detail="Category not found")

    return updated


@router.delete("/categories/{category_id}")
def delete_category(
    category_id: UUID,
    hard_delete: bool = False,
    db: Session = Depends(get_db)
):
    category_repo = CategoryRepository(db)

    # Delete category
    deleted = category_repo.delete(category_id, hard_delete=hard_delete)

    if not deleted:
        raise HTTPException(status_code=404, detail="Category not found")

    return {"message": "Category deleted successfully"}


@router.post("/categories/{category_id}/restore")
def restore_category(
    category_id: UUID,
    db: Session = Depends(get_db)
):
    category_repo = CategoryRepository(db)

    restored = category_repo.restore(category_id)

    if not restored:
        raise HTTPException(
            status_code=404,
            detail="Category not found or not deleted"
        )

    return {"message": "Category restored successfully"}
"""
