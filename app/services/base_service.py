"""
Base Service Module

This module provides a generic service pattern that wraps BaseRepository operations
with business logic validation. The service layer adds error handling
on top of the raw data access that repositories provide.

Repository returns:        Service does:
    None                       raise NotFoundException (404)
    IntegrityError             raise ConflictException (409)
    Model instance             return it as-is

These are generic defaults. Child services that need specific exceptions
(e.g., UserNotFoundException) should use the repo directly and raise them
explicitly in their own methods.

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Generic, List, NoReturn, Optional
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core.exceptions.common import ConflictException, NotFoundException
from app.models.base import ModelType
from app.repositories.base_repository import BaseRepository
from app.schemas.base import PaginationParams

if TYPE_CHECKING:
    from app.schemas.base import PaginatedResponse


class BaseService(Generic[ModelType]):
    """
    Generic service providing common CRUD operations with business logic validation.

    Wraps a BaseRepository and adds error handling on top of raw data access.
    Each concrete service should inherit from this and pass its repository to super().__init__().

    The default exceptions use the model class name for context:
        - NotFoundException(resource="User") → "User not found"
        - ConflictException → "User already exists"

    Child services that need domain-specific exceptions (e.g., UserNotFoundException)
    should use the repo directly and handle the None/error case themselves.

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
    # EXCEPTION HELPERS
    # ========================================================================

    def _raise_not_found(self) -> NoReturn:
        """Raise NotFoundException with the model class name as resource."""
        raise NotFoundException(resource=self.repo.model.__name__)

    def _raise_conflict(self) -> NoReturn:
        """Raise ConflictException with the model class name."""
        raise ConflictException(
            message=f"{self.repo.model.__name__} already exists"
        )

    # ========================================================================
    # READ OPERATIONS
    # ========================================================================

    def get_by_uuid(self, uuid: UUID) -> ModelType:
        """
        Get a record by UUID. Raises NotFoundException if not found.

        Args:
            uuid: The UUID of the record

        Returns:
            The model instance

        Raises:
            NotFoundException: If the record does not exist
        """
        instance = self.repo.get_by_uuid(uuid)
        if not instance:
            self._raise_not_found()
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
        Create a new record. Raises ConflictException on unique constraint violation.

        Args:
            data: Dictionary with field values for the new record

        Returns:
            The newly created model instance

        Raises:
            ConflictException: If creation violates a unique constraint
        """
        try:
            return self.repo.create(data)
        except IntegrityError:
            self._raise_conflict()

    # ========================================================================
    # UPDATE OPERATIONS
    # ========================================================================

    def update(self, uuid: UUID, data: Dict[str, Any]) -> ModelType:
        """
        Update a record. Raises NotFoundException if missing, ConflictException on constraint violation.

        Args:
            uuid: The UUID of the record to update
            data: Dictionary with fields to update

        Returns:
            The updated model instance

        Raises:
            NotFoundException: If the record does not exist
            ConflictException: If update violates a unique constraint
        """
        try:
            updated = self.repo.update(uuid, data)
        except IntegrityError:
            self._raise_conflict()

        if not updated:
            self._raise_not_found()

        return updated

    # ========================================================================
    # DELETE OPERATIONS
    # ========================================================================

    def delete(self, uuid: UUID) -> None:
        """
        Soft-delete a record. Raises NotFoundException if not found.

        Args:
            uuid: The UUID of the record to delete

        Raises:
            NotFoundException: If the record does not exist
        """
        deleted = self.repo.delete(uuid)

        if not deleted:
            self._raise_not_found()
