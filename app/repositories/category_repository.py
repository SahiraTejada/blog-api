from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Category
from app.repositories.base_repository import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    """
    Repository for Category model operations.

    Inherits common CRUD operations from BaseRepository and adds
    category-specific business logic.
    """

    def __init__(self, db: Session):
        super().__init__(Category, db)

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
        """
        query = self.db.query(self.model).filter(
            func.lower(self.model.name) == name.lower()
        )

        if not include_deleted:
            query = query.filter(self.model.deleted_at.is_(None))

        return query.first()

    def get_popular_categories(
        self,
        limit: int = 10,
        include_deleted: bool = False
    ) -> List[Category]:
        """
        Get the most popular categories based on post count.

        Args:
            limit: Maximum number of categories to return
            include_deleted: If True, includes soft-deleted categories

        Returns:
            List of category instances ordered by popularity

        Note:
            Currently orders by created_at. Will be updated to use post count
            when Post model relationship is implemented.
        """
        # Usa get_multi heredado del BaseRepository
        return self.get_multi(
            skip=0,
            limit=limit,
            include_deleted=include_deleted,
            order_by="created_at",
            order_desc=True
        )

    def search_categories(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[Category]:
        """
        Search categories by name or description.

        Args:
            search_term: Text to search for
            skip: Number of records to skip (pagination)
            limit: Maximum number of results

        Returns:
            List of matching category instances

        """
        # Usa el método search heredado de BaseRepository
        return self.search(
            search_fields=["name", "description"],
            search_term=search_term,
            skip=skip,
            limit=limit
        )

    def get_or_create_by_name(
        self,
        name: str,
        **kwargs
    ) -> Tuple[Category, bool]:
        """
        Get a category by name or create it if it doesn't exist.

        Args:
            name: The category name
            **kwargs: Additional fields to set when creating

        Returns:
            Tuple of (category_instance, created) where created is True
            if a new category was created
        """
        existing = self.get_by_name(name)

        if existing:
            return existing, False

        obj_in = {"name": name, **kwargs}
        new_category = self.create(obj_in)
        return new_category, True

    def get_active_categories(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Category]:
        """
        Get all active (non-deleted) categories.

        Args:
            skip: Number of records to skip (pagination)
            limit: Maximum number of categories to return

        Returns:
            List of active category instances

        Example:
            # Primera página
            categories = category_repo.get_active_categories(skip=0, limit=20)

            # Segunda página
            categories = category_repo.get_active_categories(skip=20, limit=20)
        """
        # Usa get_multi heredado con ordenamiento por nombre
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
    ) -> List[Tuple[Category, int]]:
        """
        Get categories with their associated post counts.

        Args:
            skip: Number of records to skip (pagination)
            limit: Maximum number of categories to return

        Returns:
            List of tuples (category, post_count)

        Note:
            Currently returns 0 for post count. Will be implemented when
            Post model and relationship are added.
        """
        # TODO: Implementar conteo real cuando exista el modelo Post
        categories = self.get_multi(
            skip=skip,
            limit=limit,
            include_deleted=False
        )
        return [(cat, 0) for cat in categories]

    def bulk_create_categories(self, names: List[str]) -> List[Category]:
        """
        Create multiple categories from a list of names.

        Args:
            names: List of category names to create

        Returns:
            List of created category instances

        Example:
            default_categories = [
                "Technology", "Sports", "Politics",
                "Entertainment", "Science", "Health"
            ]
            created = category_repo.bulk_create_categories(default_categories)
        """
        categories_to_create = []

        for name in names:
            # Verifica si la categoría ya existe
            existing = self.get_by_name(name)
            if not existing:
                categories_to_create.append({
                    "name": name,
                    # TODO: Agregar generación de slug
                    # "slug": generate_slug(name),
                })

        # Usa create_multi heredado de BaseRepository
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
    ) -> Optional[Category]:
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

        # TODO: Agregar generación de slug cuando esté implementado
        # if update_slug:
        #     update_data["slug"] = generate_slug(new_name)

        # Usa el método update heredado de BaseRepository
        return self.update(category_id, update_data)

    # ========================================================================
    # VALIDATION METHODS
    # ========================================================================

    def name_exists(
        self,
        name: str,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Check if a category name already exists.

        Args:
            name: The name to check
            exclude_id: Optional UUID to exclude from check (for updates)

        Returns:
            True if the name exists, False otherwise

        Example:
            # Verificar antes de crear
            if category_repo.name_exists("Technology"):
                print("Nombre de categoría ya existe")

            # Verificar antes de actualizar (excluir categoría actual)
            if category_repo.name_exists("Technology", exclude_id=current_cat_id):
                print("Otra categoría ya tiene este nombre")
        """
        query = self.db.query(self.model.uuid).filter(
            func.lower(self.model.name) == name.lower()
        ).filter(self.model.deleted_at.is_(None))

        if exclude_id:
            query = query.filter(self.model.uuid != exclude_id)

        return query.first() is not None
