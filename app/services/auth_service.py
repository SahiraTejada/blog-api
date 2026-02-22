"""
Auth Service Module

This module provides authentication-related business logic including
user registration. Token management is handled separately by TokenService.

Architecture Flow:
    Route → AuthService → UserRepository → Database

The AuthService handles:
    - User registration (create_user)
    - Credential validation (for login - delegates to TokenService for tokens)
    - Password management

Security Considerations:
    - Passwords are hashed using bcrypt before storage
    - Email and username uniqueness is enforced
    - No plain text passwords are ever stored or returned
"""

from typing import Any, Dict

from sqlalchemy.orm import Session

from app.core.exceptions import (
    EmailExistsException,
    InvalidCredentialsException,
    PasswordIncorrectException,
    UsernameExistsException,
)
from app.core.security import hash_password, verify_password
from app.models.users import User, UserRole
from app.repositories.user_repository import UserRepository
from app.services.base_service import BaseService


class AuthService(BaseService[User]):
    """
    Service for authentication operations.

    This service handles user registration and credential validation.
    Token generation/management is delegated to TokenService.

    Attributes:
        user_repo: UserRepository instance for database operations

    Example:
        auth_service = AuthService(db)
        user = auth_service.create_user(
            username="johndoe",
            email="john@example.com",
            password="SecurePass123!",
            first_name="John",
            last_name="Doe"
        )
    """

    def __init__(self, db: Session):
        """
        Initialize AuthService with database session.

        Args:
            db: SQLAlchemy database session from FastAPI dependency

        Example:
            auth_service = AuthService(db)
        """
        # Create the user repository for database operations
        self.user_repo = UserRepository(db)

        # Pass repository to BaseService for inherited CRUD methods
        super().__init__(self.user_repo)

    # ========================================================================
    # USER REGISTRATION
    # ========================================================================

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        role: UserRole = UserRole.USER
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
            user = auth_service.create_user(
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
            "role": role
        }

        # Step 5: Create user using inherited create() method
        # This handles IntegrityError → 409 if any constraint fails
        return self.create(user_data)

    # ========================================================================
    # CREDENTIAL VALIDATION
    # ========================================================================

    def login(
        self,
        email: str,
        password: str
    ) -> User:
        """
        Validate user credentials for login.

        This method only validates credentials. Token generation
        should be handled by TokenService after successful validation.

        Args:
            email: User's email address
            password: Plain text password to verify

        Returns:
            User: The authenticated user model instance

        Raises:
            InvalidCredentialsException: If email not found or password incorrect

        Example:
            # In login flow
            user = auth_service.login(
                email="john@example.com",
                password="SecurePass123!"
            )
            # Then use TokenService to create tokens
            tokens = token_service.create_token_pair(user.uuid)
        """
        # Step 1: Find user by email
        user = self.user_repo.get_by_email(email)

        # Step 2: Check if user exists
        if not user:
            # Use generic exception to prevent email enumeration
            raise InvalidCredentialsException()

        # Step 3: Verify password using bcrypt
        if not verify_password(password, user.hashed_password):
            raise InvalidCredentialsException()

        return user

    # ========================================================================
    # PASSWORD MANAGEMENT
    # ========================================================================

    def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str
    ) -> User:
        """
        Change user password.

        Requires verification of current password before allowing change.

        Args:
            user: The user model instance
            current_password: Current password for verification
            new_password: New password to set

        Returns:
            User: The updated user model instance

        Raises:
            PasswordIncorrectException: If current password is incorrect

        Example:
            updated_user = auth_service.change_password(
                user=current_user,
                current_password="OldPass123!",
                new_password="NewSecurePass456!"
            )
        """
        # Step 1: Verify current password
        if not verify_password(current_password, user.hashed_password):
            raise PasswordIncorrectException()

        # Step 2: Hash new password
        new_hashed = hash_password(new_password)

        # Step 3: Update user password
        return self.update(user.uuid, {"hashed_password": new_hashed})
