"""
Base Service Module

This module provides a generic service pattern that wraps BaseRepository operations
with business logic validation. The service layer adds HTTP-level error handling
on top of the raw data access that repositories provide.

Repository returns:        Service does:
    None                       raise HTTPException(404)
    IntegrityError             raise HTTPException(409)
    Model instance             return it as-is

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Generic, List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.models.base import ModelType
from app.repositories.base_repository import BaseRepository
from app.schemas.base import PaginationParams

if TYPE_CHECKING:
    from app.utils.pagination import PaginatedResponse


class BaseService(Generic[ModelType]):
    """
    Generic service providing common CRUD operations with business logic validation.

    Wraps a BaseRepository and adds HTTP error handling on top of raw data access.
    Each concrete service should inherit from this and pass its repository to super().__init__().

    Type Parameters:
        ModelType: The SQLAlchemy model class this service manages.

    Example:
        class PostService(BaseService[Post]):
            def __init__(self, db: Session):
                self.post_repo = PostRepository(db)
                super().__init__(self.post_repo)

            # get_by_uuid, create, update, delete are inherited
            # Add post-specific business logic below
    """

    def __init__(self, repo: BaseRepository[ModelType]):
        """Initialize BaseService with a repository instance."""
        self.repo = repo

    # ========================================================================
    # READ OPERATIONS
    # ========================================================================

    def get_by_uuid(self, uuid: UUID) -> ModelType:
        """
        Get a record by UUID. Raises 404 if not found.

        Args:
            uuid: The UUID of the record

        Returns:
            The model instance

        Raises:
            HTTPException 404: If the record does not exist
        """
        instance = self.repo.get_by_uuid(uuid)
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.repo.model.__name__} not found"
            )
        return instance

    def list(
        self,
        pagination: PaginationParams,
        filters: Optional[Dict[str, Any]] = None,
        search_fields: Optional[List[str]] = None,
        search_term: Optional[str] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False,
    ) -> PaginatedResponse[ModelType]:
        """
        List records with filtering, search, and pagination.

        Args:
            pagination: Pagination parameters (page, page_size)
            filters: Exact match filters (e.g., {"status": "PUBLISHED"})
            search_fields: Fields to search in (e.g., ["title", "content"])
            search_term: Text to search for across search_fields
            order_by: Field name to sort by
            order_desc: If True, sort descending

        Returns:
            PaginatedResponse with data and pagination metadata
        """
        return self.repo.get_multi(  # type: ignore[return-value]
            pagination=pagination,
            filters=filters,
            search_fields=search_fields,
            search_term=search_term,
            order_by=order_by,
            order_desc=order_desc,
        )

    # ========================================================================
    # CREATE OPERATIONS
    # ========================================================================

    def create(self, data: Dict[str, Any]) -> ModelType:
        """
        Create a new record. Raises 409 on unique constraint violation.

        Args:
            data: Dictionary with field values for the new record

        Returns:
            The newly created model instance

        Raises:
            HTTPException 409: If creation violates a unique constraint
        """
        try:
            return self.repo.create(data)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"{self.repo.model.__name__} already exists"
            )

    # ========================================================================
    # UPDATE OPERATIONS
    # ========================================================================

    def update(self, uuid: UUID, data: Dict[str, Any]) -> ModelType:
        """
        Update a record. Raises 404 if not found, 409 on constraint violation.

        Args:
            uuid: The UUID of the record to update
            data: Dictionary with fields to update

        Returns:
            The updated model instance

        Raises:
            HTTPException 404: If the record does not exist
            HTTPException 409: If update violates a unique constraint
        """
        self.get_by_uuid(uuid)  # raises 404 if not found

        try:
            updated = self.repo.update(uuid, data)
            return updated  # type: ignore[return-value]
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"{self.repo.model.__name__} already exists"
            )

    # ========================================================================
    # DELETE OPERATIONS
    # ========================================================================

    def delete(self, uuid: UUID) -> None:
        """
        Soft-delete a record. Raises 404 if not found.

        Args:
            uuid: The UUID of the record to delete

        Raises:
            HTTPException 404: If the record does not exist
        """
        self.get_by_uuid(uuid)  # raises 404 if not found
        self.repo.delete(uuid)
