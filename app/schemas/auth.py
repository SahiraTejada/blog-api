from pydantic import EmailStr, Field, field_validator

from app.schemas.base import BaseSchema, CreateSchema, UpdateSchema
from app.schemas.user import UserBaseSchema
from app.utils.validator_utils import validate_password, validate_username


class RegisterUserSchema(CreateSchema):
    """
    Schema for creating a new user (registration).

    This schema is used for user registration endpoints.
    Password will be hashed before storage.

    Attributes:
        username: Unique username (3-50 characters)
        email: Valid email address (will be unique)
        password: Plain text password (8-255 characters, will be hashed)
        first_name: User's first name
        last_name: User's last name
        role: User role (defaults to USER, only admins can set ADMIN)

    Example:
        {
            "username": "johndoe",
            "email": "john@example.com",
            "password": "SecurePass123!",
            "first_name": "John",
            "last_name": "Doe"
        }
    """

    username: str = Field(
        min_length=3, max_length=50, description="Unique username (3-50 characters)", json_schema_extra={"example": "johndoe"}
    )
    email: EmailStr = Field(description="Valid email address", json_schema_extra={"example": "john@example.com"})
    password: str = Field(
        min_length=8,
        max_length=255,
        description="Password (8-255 characters)",
        json_schema_extra={"example": "SecurePass123!"},
    )
    first_name: str = Field(
        min_length=1, max_length=255, description="User's first name", json_schema_extra={"example": "John"}
    )
    last_name: str = Field(min_length=1, max_length=255, description="User's last name", json_schema_extra={"example": "Doe"})

    @field_validator("username")
    @classmethod
    def check_username(cls, v: str) -> str:
        """Validate username format using utility validator."""
        result = validate_username(v)
        assert result is not None  # For type checker - validate_username without allow_none never returns None
        return result

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        """Validate password strength using utility validator."""
        return validate_password(v)


class LoginUserSchema(CreateSchema):
    """
    Schema for user login.

    This schema is used for authentication endpoints.
    Users can log in using either their username or email along with their password.

    Attributes:
        username_or_email: Username or email address
        password: Plain text password

    Example:
        {
            "username_or_email": "johndoe",
            "password": "SecurePass123!"
        }
    """

    email: EmailStr = Field(description="Email address", json_schema_extra={"example": "johndoe"})
    password: str = Field(
        min_length=8,
        max_length=255,
        description="Password (8-255 characters)",
        json_schema_extra={"example": "SecurePass123!"},
    )

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        """Validate password strength using utility validator."""
        return validate_password(v)


class UserPasswordUpdateSchema(UpdateSchema):
    """
    Schema for updating user password.

    This is a separate schema to ensure password updates are handled securely
    and require the current password for verification.

    Attributes:
        current_password: User's current password (for verification)
        new_password: New password to set

    Example:
        {
            "current_password": "OldPass123!",
            "new_password": "NewSecurePass456!"
        }
    """

    current_password: str = Field(
        description="Current password (for verification)", json_schema_extra={"example": "OldPass123!"}
    )
    new_password: str = Field(
        min_length=8,
        max_length=255,
        description="New password (8-255 characters)",
        json_schema_extra={"example": "NewSecurePass456!"},
    )

    @field_validator("new_password")
    @classmethod
    def check_new_password(cls, v: str) -> str:
        """Validate new password strength using utility validator."""
        return validate_password(v, field_name="New password")


class AuthResponseSchema(BaseSchema):
    """
    Schema for authentication response (register/login).

    Returns tokens and user information for immediate app access.

    Attributes:
        access_token: JWT access token for API authentication
        refresh_token: JWT refresh token for obtaining new access tokens
        user: Authenticated user information

    Example:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "user": {
                "uuid": "123e4567-e89b-12d3-a456-426614174000",
                "username": "johndoe",
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "role": "USER"
            }
        }
    """

    access_token: str = Field(
        description="JWT access token for API authentication",
        json_schema_extra={"example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
    )
    refresh_token: str = Field(
        description="JWT refresh token for obtaining new access tokens",
        json_schema_extra={"example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
    )
    user: UserBaseSchema = Field(
        description="Authenticated user information"
    )
