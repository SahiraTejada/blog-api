from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import User
from app.models.users import UserRole
from app.repositories.base_repository import BaseRepository
from app.schemas.base import PaginationParams

if TYPE_CHECKING:
    from app.schemas.base import PaginatedResponse


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

    def get_by_username(self, username: str, include_deleted: bool = False) -> Optional[User]:
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
        return self.get_by_text_field({"username": username}, include_deleted=include_deleted)

    def get_by_email(self, email: str, include_deleted: bool = False) -> Optional[User]:
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
        return self.get_by_text_field({"email": email}, include_deleted=include_deleted)

    def get_all_users(
        self,
        pagination: PaginationParams,
        order_by: str = "created_at",
        role: Optional[UserRole] = None,
        search_term: Optional[str] = None,
    ) -> PaginatedResponse[User]:
        """
        Get all active (non-deleted) users with filtering and pagination.

        Args:
            pagination: Pagination parameters (page, page_size)
            order_by: Field to order by. Default: "created_at"
            role: Filter users by role
            search_term: Search in username, email, first_name, and last_name

        Returns:
            PaginatedResponse with users and pagination metadata

        Example:
            pagination = PaginationParams(page=1, page_size=20)
            users = user_repo.get_all_users(pagination=pagination)

            # With filters
            admins = user_repo.get_all_users(
                pagination=pagination,
                role="admin",
                search_term="john",
            )
        """
        filters = {"role": role} if role else None
        search_fields = ["username", "email", "first_name", "last_name"] if search_term else None

        return self.get_multi(  # type: ignore[return-value]
            include_deleted=False,
            order_by=order_by,
            order_desc=False,
            pagination=pagination,
            search_fields=search_fields,
            search_term=search_term,
            filters=filters,
        )

    # ========================================================================
    # VALIDATION METHODS
    # ========================================================================

    def username_exists(
        self,
        username: str,
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
        return self.get_by_username(username) is not None

    def email_exists(
        self,
        email: str,
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
        return self.get_by_email(email) is not None

    # ========================================================================
    # GET OR CREATE METHODS
    # ========================================================================

    def get_or_create_by_email(self, email: str, defaults: Optional[dict] = None) -> Tuple[User, bool]:
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
        return self.get_or_create(email=email, defaults=defaults)

    def get_or_create_by_username(self, username: str, defaults: Optional[dict] = None) -> Tuple[User, bool]:
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
        return self.get_or_create(username=username, defaults=defaults)

    # ========================================================================
    # USER-SPECIFIC METHODS
    # ========================================================================

    def count_by_role(self, role: UserRole) -> int:
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
