from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import User
from app.repositories.base_repository import BaseRepository
from app.schemas.base import PaginatedResponse, PaginationParams


class UserRepository(BaseRepository[User]):
    """
    Repository for User model operations.

    Inherits common CRUD operations from BaseRepository and adds
    user-specific business logic.
    """

    def __init__(self, db: Session):
        """Initialize UserRepository with Users model."""
        super().__init__(User, db)

    # ========================================================================
    # USER-SPECIFIC READ METHODS
    # ========================================================================

    def get_by_username(
        self,
        username: str,
        include_deleted: bool = False
    ) -> Optional[User]:
        """
        Get a user by username (case-insensitive).

        Args:
            username: The username to find
            include_deleted: If True, includes soft-deleted users

        Returns:
            The user instance if found, None otherwise

        Example:
            user = user_repo.get_by_username("johndoe")
        """
        query = self.db.query(self.model).filter(
            func.lower(self.model.username) == username.lower()
        )

        if not include_deleted:
            query = query.filter(self.model.deleted_at.is_(None))

        return query.first()

    def get_by_email(
        self,
        email: str,
        include_deleted: bool = False
    ) -> Optional[User]:
        """
        Get a user by email (case-insensitive).

        Args:
            email: The email to find
            include_deleted: If True, includes soft-deleted users

        Returns:
            The user instance if found, None otherwise

        Example:
            user = user_repo.get_by_email("john@example.com")
        """
        query = self.db.query(self.model).filter(
            func.lower(self.model.email) == email.lower()
        )

        if not include_deleted:
            query = query.filter(self.model.deleted_at.is_(None))

        return query.first()

    def get_active_users(self, order_by: str = "created_at") -> List[User]:
        """
        Get all active (non-deleted) users ordered by specified field.

        Returns ALL active users without pagination.
        For paginated results, use get_multi_paginated() from base repository.

        Args:
            order_by: Field to order by. Default: "created_at"

        Returns:
            List of all active user instances

        Example:
            # Get all active users ordered by creation date
            users = user_repo.get_active_users()

            # Get all active users ordered by username
            users = user_repo.get_active_users(order_by="username")

            # For pagination, use get_multi_paginated:
            from app.schemas.base import PaginationParams
            pagination = PaginationParams(page=1, page_size=20)
            result = user_repo.get_multi_paginated(
                pagination=pagination,
                include_deleted=False,
                order_by="username"
            )
        """
        return self.get_multi(
            include_deleted=False,
            order_by=order_by,
            order_desc=False
        )

    def search_users(
        self,
        search_term: str,
        include_deleted: bool = False
    ) -> List[User]:
        """
        Search users by username, email, first name, or last name.

        Returns ALL matching users without pagination.
        For paginated results, use search_users_paginated().

        Args:
            search_term: Text to search for
            include_deleted: If True, includes soft-deleted users

        Returns:
            List of all matching user instances

        Example:
            # Search for users
            users = user_repo.search_users("john")

            # For paginated search:
            pagination = PaginationParams(page=1, page_size=20)
            result = user_repo.search_users_paginated("john", pagination)
        """
        return self.search(
            search_fields=["username", "email", "first_name", "last_name"],
            search_term=search_term,
            include_deleted=include_deleted
        )

    def search_users_paginated(
        self,
        search_term: str,
        pagination: PaginationParams,
        include_deleted: bool = False
    ) -> PaginatedResponse[User]:
        """
        Search users with pagination.

        Args:
            search_term: Text to search for
            pagination: PaginationParams with page and page_size
            include_deleted: If True, includes soft-deleted users

        Returns:
            PaginatedResponse with matching users and pagination metadata

        Example:
            from app.schemas.base import PaginationParams
            pagination = PaginationParams(page=1, page_size=20)
            result = user_repo.search_users_paginated("john", pagination)
        """
        return self.search_paginated(
            search_fields=["username", "email", "first_name", "last_name"],
            search_term=search_term,
            pagination=pagination,
            include_deleted=include_deleted
        )

    # ========================================================================
    # VALIDATION METHODS
    # ========================================================================

    def username_exists(
        self,
        username: str,
        exclude_uuid: Optional[UUID] = None
    ) -> bool:
        """
        Check if a username already exists (case-insensitive).

        Args:
            username: The username to check
            exclude_uuid: Optional UUID to exclude from check (for updates)

        Returns:
            True if the username exists, False otherwise

        Example:
            if user_repo.username_exists("johndoe"):
                raise HTTPException(409, "Username already taken")

            # When updating, exclude current user
            if user_repo.username_exists("johndoe", exclude_uuid=user.uuid):
                raise HTTPException(409, "Username already taken")
        """
        query = self.db.query(self.model.uuid).filter(
            func.lower(self.model.username) == username.lower()
        ).filter(self.model.deleted_at.is_(None))

        if exclude_uuid:
            query = query.filter(self.model.uuid != exclude_uuid)

        return query.first() is not None

    def email_exists(
        self,
        email: str,
        exclude_uuid: Optional[UUID] = None
    ) -> bool:
        """
        Check if an email already exists (case-insensitive).

        Args:
            email: The email to check
            exclude_uuid: Optional UUID to exclude from check (for updates)

        Returns:
            True if the email exists, False otherwise

        Example:
            if user_repo.email_exists("john@example.com"):
                raise HTTPException(409, "Email already registered")

            # When updating, exclude current user
            if user_repo.email_exists("john@example.com", exclude_uuid=user.uuid):
                raise HTTPException(409, "Email already registered")
        """
        query = self.db.query(self.model.uuid).filter(
            func.lower(self.model.email) == email.lower()
        ).filter(self.model.deleted_at.is_(None))

        if exclude_uuid:
            query = query.filter(self.model.uuid != exclude_uuid)

        return query.first() is not None

    def username_or_email_exists(
        self,
        username: str,
        email: str,
        exclude_uuid: Optional[UUID] = None
    ) -> dict:
        """
        Check if username or email already exists.

        Args:
            username: The username to check
            email: The email to check
            exclude_uuid: Optional UUID to exclude from check (for updates)

        Returns:
            Dictionary with 'username' and 'email' booleans

        Example:
            exists = user_repo.username_or_email_exists("johndoe", "john@example.com")
            if exists['username']:
                raise HTTPException(409, "Username already taken")
            if exists['email']:
                raise HTTPException(409, "Email already registered")
        """
        return {
            'username': self.username_exists(username, exclude_uuid),
            'email': self.email_exists(email, exclude_uuid)
        }

    # ========================================================================
    # GET OR CREATE METHODS
    # ========================================================================

    def get_or_create_by_email(
        self,
        email: str,
        defaults: Optional[dict] = None
    ) -> Tuple[User, bool]:
        """
        Get a user by email or create it if it doesn't exist.

        This uses the get_or_create method from BaseRepository.

        Args:
            email: The user email
            defaults: Additional fields to set when creating (optional)

        Returns:
            Tuple of (user_instance, created) where created is True
            if a new user was created

        Example:
            user, created = user_repo.get_or_create_by_email(
                email="john@example.com",
                defaults={
                    "username": "johndoe",
                    "first_name": "John",
                    "last_name": "Doe",
                    "hashed_password": "..."
                }
            )
            if created:
                print("New user created")
            else:
                print("User already existed")
        """
        return self.get_or_create(
            email=email,
            defaults=defaults
        )

    def get_or_create_by_username(
        self,
        username: str,
        defaults: Optional[dict] = None
    ) -> Tuple[User, bool]:
        """
        Get a user by username or create it if it doesn't exist.

        This uses the get_or_create method from BaseRepository.

        Args:
            username: The username
            defaults: Additional fields to set when creating (optional)

        Returns:
            Tuple of (user_instance, created) where created is True
            if a new user was created

        Example:
            user, created = user_repo.get_or_create_by_username(
                username="johndoe",
                defaults={
                    "email": "john@example.com",
                    "first_name": "John",
                    "hashed_password": "..."
                }
            )
        """
        return self.get_or_create(
            username=username,
            defaults=defaults
        )

    # ========================================================================
    # USER-SPECIFIC METHODS
    # ========================================================================

    def get_users_by_role(
        self,
        role: str,
        include_deleted: bool = False
    ) -> List[User]:
        """
        Get all users with a specific role.

        Args:
            role: The role to filter by (e.g., "admin", "user")
            include_deleted: If True, includes soft-deleted users

        Returns:
            List of users with the specified role

        Example:
            admins = user_repo.get_users_by_role("admin")
        """
        return self.filter_by(
            role=role,
            include_deleted=include_deleted
        )

    def count_by_role(self, role: str) -> int:
        """
        Count users by role.

        Args:
            role: The role to count

        Returns:
            Number of users with the specified role

        Example:
            admin_count = user_repo.count_by_role("admin")
        """
        return self.count(filters={"role": role})
