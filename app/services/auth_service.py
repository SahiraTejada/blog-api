"""
Auth Service Module

This module provides authentication-related business logic including
user registration. Token management is handled separately by TokenService.

Architecture Flow:
    Route → AuthService → UserRepository → Database

The AuthService handles:
    - User registration (register)
    - Credential validation (login)
    - Password management

Security Considerations:
    - Passwords are hashed using bcrypt before storage
    - Email and username uniqueness is enforced
    - No plain text passwords are ever stored or returned
"""

from typing import Dict, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.exceptions import (
    InvalidCredentialsException,
    PasswordIncorrectException,
)
from app.core.security import hash_password, verify_password
from app.models.tokens import Token
from app.models.users import User, UserRole
from app.repositories.user_repository import UserRepository
from app.services.base_service import BaseService
from app.services.token_service import TokenService
from app.services.user_service import UserService


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
        self.user_repo = UserRepository(db)
        self.token_service = TokenService(db)
        self.user_service = UserService(db)

        # Pass repository to BaseService for inherited CRUD methods
        super().__init__(self.user_repo)

    # ========================================================================
    # USER REGISTRATION
    # ========================================================================

    def register(
        self,
        username: str,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        role: UserRole = UserRole.USER,
        ip_address: Optional[str] = None
    ) -> Tuple[User, Dict[str, Token]]:
        """
        Register a new user and create tokens.

        Args:
            username: Unique username
            email: Unique email address
            password: Plain text password (will be hashed)
            first_name: User's first name
            last_name: User's last name
            role: User role (default: USER)
            ip_address: Client IP for token tracking

        Returns:
            Tuple of (User, tokens_dict) where tokens_dict has 'access' and 'refresh'

        Raises:
            UsernameExistsException: If username already exists
            EmailExistsException: If email already exists
        """
        # Create user
        user = self.user_service.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role,
        )

        # Create tokens
        tokens = self.token_service.create_token_pair(
            user_uuid=user.uuid,
            ip_address=ip_address,
        )

        return user, tokens

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
        # Step 1: Find user by email using repo directly
        # to avoid UserNotFoundException leaking email existence
        user = self.user_repo.get_by_email(email)

        # Step 2: Check if user exists
        if not user:
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
        return self.user_service.update(user.uuid, {"hashed_password": new_hashed})
