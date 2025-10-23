"""
Base Repository Module

This module provides a generic repository pattern implementation for database operations.
The repository pattern abstracts the data access layer, providing a clean separation
between business logic and data access code.

Benefits:
- Centralized data access logic
- Reduced code duplication
- Easier testing (can mock repositories)
- Consistent error handling
- Simplified query building

"""

from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, cast
from uuid import UUID

from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.base import BaseModel
from app.schemas.base import PaginationParams
from app.utils.pagination import paginate, PaginatedResponse

# ======================== , ====================================================
# TYPE VARIABLES
# ============================================================================
# TypeVar allows us to create generic classes that work with any model type.
# This enables type safety while maintaining flexibility.

ModelType = TypeVar("ModelType", bound=BaseModel)
# ModelType is bound to BaseModel, meaning it must be a subclass of BaseModel.
# This ensures our repository only works with valid database models.


# ============================================================================
# BASE REPOSITORY CLASS
# ============================================================================

class BaseRepository(Generic[ModelType]):
    """
    Generic repository providing CRUD operations for any SQLAlchemy model.

    This class implements the Repository Pattern, which mediates between
    the domain and data mapping layers using a collection-like interface
    for accessing domain objects.

    Type Parameters:
        ModelType: The SQLAlchemy model class this repository manages.
                   Must inherit from BaseModel.

    Attributes:
        model: The SQLAlchemy model class
        db: The database session for executing queries

    Example usage:
        # Create a repository for a specific model
        user_repo = BaseRepository(User, db_session)

        # Get a user by ID
        user = user_repo.get(user_id)

        # Create a new user
        new_user = user_repo.create({"email": "test@example.com", "name": "Test"})

        # Update a user
        updated_user = user_repo.update(user_id, {"name": "Updated Name"})

        # Delete a user (soft delete)
        user_repo.delete(user_id)
    """

    def __init__(self, model: Type[ModelType], db: Session):
        """
        Initialize the repository with a model class and database session.

        Args:
            model: The SQLAlchemy model class this repository will manage
            db: SQLAlchemy database session for executing queries
        """
        self.model = model
        self.db = db

    # ========================================================================
    # READ OPERATIONS
    # ========================================================================

    def get(
        self,
        uuid: UUID,
        include_deleted: bool = False
    ) -> Optional[ModelType]:
        """
        Retrieve a single record by its primary key (UUID).

        This method fetches a single entity from the database using its unique
        identifier. By default, it only returns non-deleted records (soft delete).

        Args:
            id: The UUID of the record to retrieve
            include_deleted: If True, includes soft-deleted records in the search.
                           Default is False (only active records).

        Returns:
            The model instance if found, None otherwise

        Example:
            user = user_repository.get(user_uuid)
            if user:
                print(f"Found user: {user.email}")
            else:
                print("User not found")

        """
        query = self.db.query(self.model).filter(self.model.uuid == uuid)

        # Apply soft delete filter unless explicitly requested to include deleted
        if not include_deleted:
            query = query.filter(self.model.deleted_at.is_(None))

        return query.first()

    def get_multi(
        self,
        include_deleted: bool = False,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> List[ModelType]:
        """
        Retrieve multiple records with pagination, filtering, and sorting.

        This is the main method for fetching collections of records. It supports:
        - Pagination (skip/limit)
        - Soft delete filtering
        - Dynamic field filtering
        - Sorting

        Args:
            skip: Number of records to skip (for pagination). Default is 0.
            limit: Maximum number of records to return. Default is 100.
            include_deleted: If True, includes soft-deleted records. Default is False.
            filters: Dictionary of field-value pairs to filter by.
                    Example: {"email": "test@example.com", "is_active": True}
            order_by: Field name to sort by. Default is None (no specific ordering).
            order_desc: If True, sorts in descending order. Default is False (ascending).

        Returns:
            List of model instances matching the criteria

        Note:
            The limit parameter prevents accidentally fetching huge datasets.
            Adjust as needed for your use case.
        """
        query = self.db.query(self.model)

        # Apply soft delete filter
        if not include_deleted:
            query = query.filter(self.model.deleted_at.is_(None))

        # Apply dynamic filters
        if filters:
            for field, value in filters.items():
                # Check if the model has the specified field
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)

        # Apply sorting
        if order_by and hasattr(self.model, order_by):
            order_column = getattr(self.model, order_by)
            if order_desc:
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())

        return query.all()

    def get_multi_paginated(
        self,
        pagination: PaginationParams,
        include_deleted: bool = False,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> PaginatedResponse[Any]:
        """
        Retrieve multiple records with automatic pagination using PaginationParams.

        This method returns a paginated response with both the data and pagination
        metadata. It uses the pagination utilities to automatically calculate
        all pagination information.

        Args:
            pagination: PaginationParams object with page and page_size
            include_deleted: If True, includes soft-deleted records. Default is False.
            filters: Dictionary of field-value pairs to filter by.
            order_by: Field name to sort by. Default is None (no specific ordering).
            order_desc: If True, sorts in descending order. Default is False (ascending).

        Returns:
            PaginatedResponse containing:
                - data: List of model instances for the current page
                - pagination: PaginationMeta with page info

        Example:
            pagination_params = PaginationParams(page=1, page_size=20)
            result = user_repository.get_multi_paginated(
                pagination=pagination_params,
                filters={"is_active": True},
                order_by="created_at",
                order_desc=True
            )

            # Access data
            users = result.data

            # Access pagination info
            print(f"Page {result.pagination.page} of {result.pagination.total_pages}")
            print(f"Total users: {result.pagination.total_items}")

        Note:
            This method automatically handles skip/limit calculation and
            provides complete pagination metadata for the frontend.
        """
        # Get the items for the current page
        items = self.get_multi(
            include_deleted=include_deleted,
            filters=filters,
            order_by=order_by,
            order_desc=order_desc
        )

        # Get total count with same filters
        total_count = self.count(
            include_deleted=include_deleted,
            filters=filters
        )

        # Return paginated response
        return paginate(items, pagination, total_count)

    def get_all(self, include_deleted: bool = False) -> List[ModelType]:
        """
        Retrieve all records from the table.

        WARNING: Use with caution on large tables! This fetches ALL records
        without pagination, which can cause memory issues and slow performance.

        Args:
            include_deleted: If True, includes soft-deleted records. Default is False.

        Returns:
            List of all model instances

        Example:
            all_users = user_repository.get_all()

        Recommendation:
            For production applications, prefer get_multi() with pagination
            to avoid loading too much data into memory.
        """
        query = self.db.query(self.model)

        if not include_deleted:
            query = query.filter(self.model.deleted_at.is_(None))

        return query.all()

    def count(
        self,
        include_deleted: bool = False,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count the total number of records matching the criteria.

        Useful for pagination (calculating total pages) and statistics.

        Args:
            include_deleted: If True, includes soft-deleted records in count.
            filters: Dictionary of field-value pairs to filter by

        Returns:
            Integer count of matching records

        Example:
            # Count active users
            total_users = user_repository.count(filters={"is_active": True})
            total_pages = (total_users + page_size - 1) // page_size
        """
        query = self.db.query(func.count(self.model.uuid))

        if not include_deleted:
            query = query.filter(self.model.deleted_at.is_(None))

        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)

        return query.scalar() or 0

    def exists(
        self,
        uuid: UUID,
        include_deleted: bool = False
    ) -> bool:
        """
        Check if a record exists by its ID.

        This is more efficient than get() when you only need to verify existence
        without loading the entire record.

        Args:
            id: The UUID of the record to check
            include_deleted: If True, considers deleted records as existing

        Returns:
            True if the record exists, False otherwise

        Example:
            if user_repository.exists(user_uuid):
                print("User exists")
            else:
                print("User not found")
        """
        query = self.db.query(self.model.uuid).filter(self.model.uuid == uuid)

        if not include_deleted:
            query = query.filter(self.model.deleted_at.is_(None))

        return query.first() is not None

    def filter_by(
        self,
        include_deleted: bool = False,
        **kwargs: Any
    ) -> List[ModelType]:
        """
        Filter records using keyword arguments.

        This provides a convenient way to filter by exact field matches
        using Python keyword arguments instead of a dictionary.

        Args:
            include_deleted: If True, includes soft-deleted records
            **kwargs: Field-value pairs to filter by

        Returns:
            List of model instances matching all the specified criteria

        Example:
            # Find all active users with a specific email
            users = user_repository.filter_by(
                email="test@example.com",
                is_active=True
            )

        Note:
            This performs an AND operation on all filters (all must match).
        """
        query = self.db.query(self.model)

        if not include_deleted:
            query = query.filter(self.model.deleted_at.is_(None))

        # Apply each filter
        for field, value in kwargs.items():
            if hasattr(self.model, field):
                query = query.filter(getattr(self.model, field) == value)

        return query.all()

    # ========================================================================
    # CREATE OPERATIONS
    # ========================================================================

    def create(self, obj_in: Dict[str, Any]) -> ModelType:
        """
        Create a new record in the database.

        This method instantiates a new model instance, adds it to the session,
        commits the transaction, and returns the created object with all
        database-generated fields (like UUID, timestamps) populated.

        Args:
            obj_in: Dictionary containing the field values for the new record

        Returns:
            The newly created model instance with all fields populated

        Raises:
            IntegrityError: If the data violates database constraints
                           (e.g., unique constraints, foreign key constraints)
            SQLAlchemyError: For other database errors


        Note:
            - The method automatically commits the transaction
            - If an error occurs, the transaction is rolled back
            - After commit, the object is refreshed to get DB-generated values
        """
        try:
            # Create a new instance of the model with the provided data
            db_obj = self.model(**obj_in)

            # Add the instance to the session (marks it for insert)
            self.db.add(db_obj)

            # Commit the transaction (actually writes to the database)
            self.db.commit()

            # Refresh to get any database-generated values (UUID, timestamps, etc.)
            self.db.refresh(db_obj)

            return db_obj

        except IntegrityError as e:
            # Rollback the transaction if there's a constraint violation
            self.db.rollback()
            # Re-raise the exception so the caller can handle it
            raise e
        except SQLAlchemyError as e:
            # Rollback for any other database error
            self.db.rollback()
            raise e

    def create_multi(self, objs_in: List[Dict[str, Any]]) -> List[ModelType]:
        """
        Create multiple records in a single transaction.

        This is more efficient than calling create() multiple times because:
        - All records are inserted in one database transaction
        - Reduces database round trips
        - All succeed or all fail (atomicity)

        Args:
            objs_in: List of dictionaries, each containing field values for a record

        Returns:
            List of newly created model instances

        Raises:
            IntegrityError: If any record violates database constraints
            SQLAlchemyError: For other database errors

        Example:
            new_users = user_repository.create_multi([
                {"email": "user1@example.com", "name": "User 1"},
                {"email": "user2@example.com", "name": "User 2"},
                {"email": "user3@example.com", "name": "User 3"}
            ])
            print(f"Created {len(new_users)} users")

        Note:
            If any record fails validation, the entire operation is rolled back
            and none of the records are created (transaction atomicity).
        """
        try:
            # Create instances for all objects
            db_objs = [self.model(**obj_data) for obj_data in objs_in]

            # Add all instances to the session
            self.db.add_all(db_objs)

            # Commit the transaction (all inserts happen together)
            self.db.commit()

            # Refresh all objects to get database-generated values
            for db_obj in db_objs:
                self.db.refresh(db_obj)

            return db_objs

        except IntegrityError as e:
            self.db.rollback()
            raise e
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e

    # ========================================================================
    # UPDATE OPERATIONS
    # ========================================================================

    def update(
        self,
        uuid: UUID,
        obj_in: Dict[str, Any]
    ) -> Optional[ModelType]:
        """
        Update an existing record.

        This method fetches the record by ID, updates the specified fields,
        and commits the changes to the database. The updated_at timestamp
        is automatically updated by the BaseModel.

        Args:
            id: The UUID of the record to update
            obj_in: Dictionary containing the fields to update and their new values

        Returns:
            The updated model instance, or None if the record was not found

        Raises:
            IntegrityError: If the updated data violates database constraints
            SQLAlchemyError: For other database errors

        Example:
            updated_user = user_repository.update(
                user_uuid,
                {"name": "Updated Name", "is_active": False}
            )
            if updated_user:
                print(f"Updated user: {updated_user.name}")
            else:
                print("User not found")

        Note:
            - Only the fields present in obj_in are updated
            - Other fields remain unchanged
            - Returns None if the record doesn't exist or is soft-deleted
        """
        # Fetch the existing record
        db_obj = self.get(uuid)

        if not db_obj:
            return None

        try:
            # Update each field specified in obj_in
            for field, value in obj_in.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)

            # Commit the changes
            self.db.commit()

            # Refresh to get updated values (like updated_at timestamp)
            self.db.refresh(db_obj)

            return db_obj

        except IntegrityError as e:
            self.db.rollback()
            raise e
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e

    def update_multi(
        self,
        filters: Dict[str, Any],
        obj_in: Dict[str, Any]
    ) -> int:
        """
        Update multiple records matching the specified filters.

        This performs a bulk update operation, which is much more efficient
        than updating records one by one. It's useful for batch operations.

        Args:
            filters: Dictionary of field-value pairs to identify records to update
            obj_in: Dictionary of field-value pairs to update

        Returns:
            Number of records updated

        Raises:
            SQLAlchemyError: For database errors

        Example:
            # Deactivate all users with a specific domain
            count = user_repository.update_multi(
                filters={"email_domain": "oldcompany.com"},
                obj_in={"is_active": False}
            )
            print(f"Deactivated {count} users")

        Warning:
            This method bypasses Python-level validations and directly
            updates the database. Use with caution.
        """
        try:
            query = self.db.query(self.model)

            # Build the filter conditions
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)

            # Exclude soft-deleted records
            query = query.filter(self.model.deleted_at.is_(None))

            # Add updated_at timestamp
            update_values = {**obj_in, "updated_at": datetime.now(timezone.utc)}

            # Perform the bulk update
            count = query.update(update_values, synchronize_session=False)  # type: ignore[arg-type]

            self.db.commit()

            return count

        except SQLAlchemyError as e:
            self.db.rollback()
            raise e

    # ========================================================================
    # DELETE OPERATIONS
    # ========================================================================

    def delete(
        self,
        uuid: UUID,
        hard_delete: bool = False
    ) -> bool:
        """
        Delete a record (soft delete by default).

        Soft Delete (default):
            Sets the deleted_at timestamp without actually removing the record.
            The record is hidden from normal queries but remains in the database.
            This allows for data recovery and maintains referential integrity.

        Hard Delete:
            Permanently removes the record from the database.
            This cannot be undone and may cause foreign key errors if other
            records reference this one.

        Args:
            id: The UUID of the record to delete
            hard_delete: If True, permanently removes the record. Default is False.

        Returns:
            True if the record was deleted, False if not found

        Raises:
            IntegrityError: If hard delete violates foreign key constraints
            SQLAlchemyError: For other database errors

        Example:
            # Soft delete (default)
            user_repository.delete(user_uuid)

            # Hard delete (permanent)
            user_repository.delete(user_uuid, hard_delete=True)

        Note:
            Soft-deleted records can be restored using restore() method.
        """
        db_obj = self.get(uuid)

        if not db_obj:
            return False

        try:
            if hard_delete:
                # Permanently delete the record
                self.db.delete(db_obj)
            else:
                # Soft delete: just set the deleted_at timestamp
                setattr(db_obj, 'deleted_at', datetime.now(timezone.utc))

            self.db.commit()
            return True

        except IntegrityError as e:
            self.db.rollback()
            raise e
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e

    def delete_multi(
        self,
        filters: Dict[str, Any],
        hard_delete: bool = False
    ) -> int:
        """
        Delete multiple records matching the specified filters.

        Args:
            filters: Dictionary of field-value pairs to identify records to delete
            hard_delete: If True, permanently removes records. Default is False.

        Returns:
            Number of records deleted

        Raises:
            IntegrityError: If hard delete violates constraints
            SQLAlchemyError: For other database errors

        Example:
            # Soft delete all inactive users
            count = user_repository.delete_multi(
                filters={"is_active": False}
            )
            print(f"Deleted {count} inactive users")

        Warning:
            Be careful with filters to avoid accidentally deleting too many records.
        """
        try:
            query = self.db.query(self.model)

            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)

            # Don't delete already deleted records
            query = query.filter(self.model.deleted_at.is_(None))

            if hard_delete:
                count = query.delete(synchronize_session=False)
            else:
                count = query.update(
                    {"deleted_at": datetime.now(timezone.utc)},
                    synchronize_session=False
                )

            self.db.commit()
            return count

        except IntegrityError as e:
            self.db.rollback()
            raise e
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e

    def restore(self, uuid: UUID) -> bool:
        """
        Restore a soft-deleted record.

        This method undeletes a record by clearing its deleted_at timestamp,
        making it visible in normal queries again.

        Args:
            id: The UUID of the record to restore

        Returns:
            True if the record was restored, False if not found or not deleted

        Raises:
            SQLAlchemyError: For database errors

        Example:
            # Restore a deleted user
            if user_repository.restore(user_uuid):
                print("User restored successfully")
            else:
                print("User not found or was not deleted")

        Note:
            This only works for soft-deleted records. Hard-deleted records
            cannot be restored.
        """
        # Look for the record including deleted ones
        db_obj = self.get(uuid, include_deleted=True)

        if not db_obj or db_obj.deleted_at is None:
            return False

        try:
            # Clear the deleted_at timestamp
            setattr(db_obj, 'deleted_at', None)
            self.db.commit()
            return True

        except SQLAlchemyError as e:
            self.db.rollback()
            raise e

    # ========================================================================
    # ADVANCED QUERY OPERATIONS
    # ========================================================================

    def search(
        self,
        search_fields: List[str],
        search_term: str,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[ModelType]:
        """
        Search for records where any of the specified fields contain the search term.

        This performs a case-insensitive partial match on text fields.
        Useful for implementing search functionality in your API.

        Args:
            search_fields: List of field names to search in
            search_term: The text to search for
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            include_deleted: If True, includes soft-deleted records

        Returns:
            List of model instances matching the search criteria

        Example:
            # Search for users by name or email
            results = user_repository.search(
                search_fields=["name", "email"],
                search_term="john",
                limit=20
            )

        Note:
            This uses SQL ILIKE operator for case-insensitive pattern matching.
            For large datasets, consider using full-text search or search engines.
        """
        query = self.db.query(self.model)

        if not include_deleted:
            query = query.filter(self.model.deleted_at.is_(None))

        # Build OR conditions for all search fields
        search_conditions = []
        for field in search_fields:
            if hasattr(self.model, field):
                # Use ilike for case-insensitive partial matching
                # The % wildcards allow matching anywhere in the field
                search_conditions.append(
                    getattr(self.model, field).ilike(f"%{search_term}%")
                )

        if search_conditions:
            # Apply OR condition (match any of the fields)
            query = query.filter(or_(*search_conditions))

        return query.offset(skip).limit(limit).all()

    def search_paginated(
        self,
        search_fields: List[str],
        search_term: str,
        pagination: PaginationParams,
        include_deleted: bool = False
    ) -> PaginatedResponse[Any]:
        """
        Search for records with automatic pagination.

        This method performs a case-insensitive partial match on text fields
        and returns a paginated response with metadata.

        Args:
            search_fields: List of field names to search in
            search_term: The text to search for
            pagination: PaginationParams object with page and page_size
            include_deleted: If True, includes soft-deleted records

        Returns:
            PaginatedResponse containing:
                - data: List of matching model instances for current page
                - pagination: PaginationMeta with page info

        Example:
            pagination_params = PaginationParams(page=1, page_size=20)
            result = user_repository.search_paginated(
                search_fields=["name", "email"],
                search_term="john",
                pagination=pagination_params
            )

            # Access data
            matching_users = result.data

            # Access pagination info
            print(f"Found {result.pagination.total_items} matching users")
            print(f"Showing page {result.pagination.page}")

        Note:
            This uses SQL ILIKE operator for case-insensitive pattern matching.
            For large datasets, consider using full-text search.
        """
        # Get the items for the current page
        items = self.search(
            search_fields=search_fields,
            search_term=search_term,
            skip=pagination.skip,
            limit=pagination.limit,
            include_deleted=include_deleted
        )

        # Count total matching items
        query = self.db.query(self.model)

        if not include_deleted:
            query = query.filter(self.model.deleted_at.is_(None))

        # Build search conditions
        search_conditions = []
        for field in search_fields:
            if hasattr(self.model, field):
                search_conditions.append(
                    getattr(self.model, field).ilike(f"%{search_term}%")
                )

        if search_conditions:
            query = query.filter(or_(*search_conditions))

        total_count = query.count()

        # Return paginated response
        return paginate(items, pagination, total_count)

    def get_or_create(
        self,
        defaults: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> tuple[ModelType, bool]:
        """
        Get an existing record or create a new one if it doesn't exist.

        This is an atomic operation useful for ensuring a record exists
        without worrying about race conditions or duplicate creation.

        Args:
            defaults: Dictionary of additional field values to use when creating
            **kwargs: Field-value pairs to search for and include in creation

        Returns:
            Tuple of (instance, created) where:
                - instance is the model instance (existing or newly created)
                - created is True if a new record was created, False if existing

        Raises:
            IntegrityError: If creation violates database constraints
            SQLAlchemyError: For other database errors

        Example:
            # Get or create a category
            category, created = category_repository.get_or_create(
                name="Technology",
                defaults={"description": "Tech related posts"}
            )
            if created:
                print("Created new category")
            else:
                print("Category already existed")

        Note:
            The kwargs are used both for searching and for creating the record.
            The defaults are only used when creating a new record.
        """
        # Try to find an existing record
        instance = self.filter_by(**kwargs)

        if instance:
            # Return the first matching record
            return instance[0], False

        # Record doesn't exist, create it
        try:
            # Combine kwargs and defaults for creation
            obj_in = {**kwargs}
            if defaults:
                obj_in.update(defaults)

            instance = self.create(obj_in)
            return instance, True

        except IntegrityError as e:
            # Another process might have created the record between our
            # check and insert. Try to get it one more time.
            self.db.rollback()
            instance = self.filter_by(**kwargs)
            if instance:
                return instance[0], False
            # If still not found, raise the original error
            raise e

    def bulk_create_or_update(
        self,
        objs_in: List[Dict[str, Any]],
        match_fields: List[str]
    ) -> tuple[List[ModelType], int, int]:
        """
        Bulk upsert operation: create new records or update existing ones.

        This is useful for synchronization tasks or importing data where
        some records might already exist.

        Args:
            objs_in: List of dictionaries with record data
            match_fields: List of field names to use for matching existing records

        Returns:
            Tuple of (instances, created_count, updated_count) where:
                - instances is a list of all model instances
                - created_count is the number of new records created
                - updated_count is the number of existing records updated

        Raises:
            SQLAlchemyError: For database errors

        Example:
            # Sync categories from external source
            categories_data = [
                {"name": "Tech", "description": "Technology posts"},
                {"name": "Sports", "description": "Sports posts"}
            ]
            instances, created, updated = category_repository.bulk_create_or_update(
                objs_in=categories_data,
                match_fields=["name"]
            )
            print(f"Created: {created}, Updated: {updated}")

        Note:
            This operates in a single transaction for consistency.
        """
        instances = []
        created_count = 0
        updated_count = 0

        try:
            for obj_data in objs_in:
                # Build match filters from specified fields
                match_filters = {
                    field: obj_data[field]
                    for field in match_fields
                    if field in obj_data
                }

                # Try to find existing record
                existing = self.filter_by(**match_filters)

                if existing:
                    # Update existing record
                    existing_uuid = cast(UUID, existing[0].uuid)
                    updated = self.update(existing_uuid, obj_data)
                    if updated:
                        instances.append(updated)
                        updated_count += 1
                else:
                    # Create new record
                    new_obj = self.model(**obj_data)
                    self.db.add(new_obj)
                    instances.append(new_obj)
                    created_count += 1

            # Commit all changes at once
            self.db.commit()

            # Refresh all new objects
            for obj in instances[len(instances) - created_count:]:
                self.db.refresh(obj)

            return instances, created_count, updated_count

        except SQLAlchemyError as e:
            self.db.rollback()
            raise e

    # ========================================================================
    # UTILITY OPERATIONS
    # ========================================================================

    def refresh(self, db_obj: ModelType) -> ModelType:
        """
        Refresh an object from the database.

        This reloads the object's attributes from the database, discarding
        any uncommitted changes. Useful when you need to ensure you have
        the latest data.

        Args:
            db_obj: The model instance to refresh

        Returns:
            The refreshed model instance

        Example:
            user = user_repository.get(user_uuid)
            # ... some time passes and data might have changed ...
            user = user_repository.refresh(user)
            print("Refreshed user data")
        """
        self.db.refresh(db_obj)
        return db_obj

    def expunge(self, db_obj: ModelType) -> ModelType:
        """
        Remove an object from the session without deleting it.

        After expunging, the object is no longer associated with the session,
        and changes to it won't be tracked or saved. Useful for detaching
        objects that you want to modify without affecting the database.

        Args:
            db_obj: The model instance to expunge

        Returns:
            The expunged model instance

        Example:
            user = user_repository.get(user_uuid)
            user = user_repository.expunge(user)
            user.name = "Modified"  # This change won't be saved
        """
        self.db.expunge(db_obj)
        return db_obj

    def __repr__(self) -> str:
        """
        String representation of the repository.

        Returns:
            A string describing this repository instance
        """
        return f"<{self.__class__.__name__}(model={self.model.__name__})>"
