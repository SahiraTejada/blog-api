"""
User Service Module

This module provides user management business logic including
user creation, retrieval, and profile updates.

Architecture Flow:
    Route → UserService → UserRepository → Database

The UserService handles:
    - User creation (create_user)
    - User retrieval by UUID, username, or email
    - User profile updates

Security Considerations:
    - Passwords are hashed using bcrypt before storage
    - Email and username uniqueness is enforced
    - No plain text passwords are ever stored or returned
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import (
    EmailExistsException,
    UsernameExistsException,
)
from app.core.exceptions.user import UserNotFoundException
from app.core.security import hash_password
from app.models.users import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.base import PaginationParams
from app.services.base_service import BaseService

if TYPE_CHECKING:
    from app.schemas.base import PaginatedResponse


class UserService(BaseService[User]):
    """
    Service for user management operations.

    This service handles user creation, retrieval, and profile updates.

    Attributes:
        user_repo: UserRepository instance for database operations

    Example:
        user_service = UserService(db)
        user = user_service.create_user(
            username="johndoe",
            email="john@example.com",
            password="SecurePass123!",
            first_name="John",
            last_name="Doe"
        )
    """

    def __init__(self, db: Session):
        """
        Initialize UserService with database session.

        Args:
            db: SQLAlchemy database session from FastAPI dependency

        Example:
            user_service = UserService(db)
        """
        self.user_repo = UserRepository(db)

        super().__init__(self.user_repo)

    # ========================================================================
    # USER REGISTRATION
    # ========================================================================

    def create_user(
        self, username: str, email: str, password: str, first_name: str, last_name: str, role: UserRole = UserRole.USER
    ) -> User:
        """
        Create a new user (registration).

        This method:
        1. Validates username and email are unique
        2. Hashes the password using bcrypt
        3. Creates the user in the database

        Args:
            username: Unique username (3-50 characters)
            email: Unique email address
            password: Plain text password (will be hashed)
            first_name: User's first name
            last_name: User's last name
            role: User role (default: USER)

        Returns:
            User: The created user model instance

        Raises:
            UsernameExistsException: If username already exists
            EmailExistsException: If email already exists

        Example:
            user = user_service.create_user(
                username="johndoe",
                email="john@example.com",
                password="SecurePass123!",
                first_name="John",
                last_name="Doe"
            )
        """
        # Step 1: Check if username already exists
        if self.user_repo.username_exists(username):
            raise UsernameExistsException()

        # Step 2: Check if email already exists
        if self.user_repo.email_exists(email):
            raise EmailExistsException()

        # Step 3: Hash the password using bcrypt
        # Never store plain text passwords
        hashed = hash_password(password)

        # Step 4: Prepare user data for creation
        user_data: Dict[str, Any] = {
            "username": username,
            "email": email.lower(),  # Normalize email to lowercase
            "hashed_password": hashed,
            "first_name": first_name,
            "last_name": last_name,
            "role": role,
        }

        # Step 5: Create user using inherited create() method
        # This handles IntegrityError → 409 if any constraint fails
        return self.create(user_data)

    def get_by_user_uuid(self, user_uuid: UUID) -> User:
        """
        Get user by UUID.

        Args:
            user_uuid: UUID of the user to retrieve

        Returns:
            User: The user model instance

        Raises:
            UserNotFoundException: If user with given UUID does not exist
        """
        user = self.user_repo.get_by_uuid(user_uuid)

        if not user:
            raise UserNotFoundException()

        return user

    def get_by_username(self, username: str) -> User:
        """
        Get user by username.

        Args:
            username: The username of the user to retrieve

        Returns:
            User: The user model instance

        Raises:
            UserNotFoundException: If user with given username does not exist
        """
        user = self.user_repo.get_by_username(username)

        if not user:
            raise UserNotFoundException()

        return user

    def get_by_email(self, email: str) -> User:
        """
        Get user by email.

        Args:
            email: The email of the user to retrieve

        Returns:
            User: The user model instance

        Raises:
            UserNotFoundException: If user with given email does not exist
        """
        user = self.user_repo.get_by_email(email)

        if not user:
            raise UserNotFoundException()

        return user

    def get_all_users(
        self,
        pagination: PaginationParams,
        order_by: str = "created_at",
        role: Optional[UserRole] = None,
        search_term: Optional[str] = None,
    ) -> PaginatedResponse[User]:
        """
        Get all active users with optional filtering, search, and pagination.

        Args:
            pagination: Pagination parameters (page, page_size)
            order_by: Field to order by (default: "created_at")
            role: Filter users by role (USER, ADMIN)
            search_term: Search in username, email, first_name, and last_name

        Returns:
            PaginatedResponse with users and pagination metadata
        """
        return self.user_repo.get_all_users(
            pagination=pagination,
            order_by=order_by,
            role=role,
            search_term=search_term,
        )

    def update_user(self, user_uuid: UUID, update_data: Dict[str, Any]) -> User:
        """
        Update user information.

        Args:
            user_uuid: UUID of the user to update
            update_data: Dictionary of fields to update (e.g., first_name, last_name)

        Returns:
            User: The updated user model instance

        Raises:
            UserNotFoundException: If user with given UUID does not exist
            UsernameExistsException: If new username already exists
            EmailExistsException: If new email already exists

        Example:
            updated_user = user_service.update_user(
                user_uuid=UUID("123e4567-e89b-12d3-a456-426614174000"),
                update_data={"first_name": "Jane", "last_name": "Smith"}
            )
        """
        # Verify user exists
        user = self.user_repo.get_by_uuid(user_uuid)

        if not user:
            raise UserNotFoundException()

        # Validate username uniqueness if being updated
        new_username = update_data.get("username")
        if new_username and new_username != user.username:
            if self.user_repo.username_exists(new_username):
                raise UsernameExistsException()

        # Validate email uniqueness if being updated
        new_email = update_data.get("email")
        if new_email and new_email.lower() != user.email.lower():
            if self.user_repo.email_exists(new_email):
                raise EmailExistsException()
            update_data["email"] = new_email.lower()

        updated_user = self.user_repo.update(user_uuid, update_data)

        if not updated_user:
            raise UserNotFoundException()

        return updated_user

    def delete_user(self, user_uuid: UUID) -> None:
        """
        Soft-delete a user.

        Args:
            user_uuid: UUID of the user to delete

        Raises:
            UserNotFoundException: If user with given UUID does not exist
        """
        deleted = self.user_repo.delete(user_uuid)

        if not deleted:
            raise UserNotFoundException()
