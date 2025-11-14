from typing import Optional

from pydantic import EmailStr, Field, field_validator

from app.models.users import UserRole
from app.schemas.base import CreateSchema, ResponseSchema, UpdateSchema
from app.utils.validator_utils import validate_password, validate_username


class UserCreateSchema(CreateSchema):
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
        min_length=3,
        max_length=50,
        description="Unique username (3-50 characters)",
        json_schema_extra={"example": "johndoe"}
    )
    email: EmailStr = Field(
        description="Valid email address",
        json_schema_extra={"example": "john@example.com"}
    )
    password: str = Field(
        min_length=8,
        max_length=255,
        description="Password (8-255 characters)",
        json_schema_extra={"example": "SecurePass123!"}
    )
    first_name: str = Field(
        min_length=1,
        max_length=255,
        description="User's first name",
        json_schema_extra={"example": "John"}
    )
    last_name: str = Field(
        min_length=1,
        max_length=255,
        description="User's last name",
        json_schema_extra={"example": "Doe"}
    )
    role: Optional[UserRole] = Field(
        default=UserRole.USER,
        description="User role (defaults to USER)"
    )

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


class UserUpdateSchema(UpdateSchema):
    """
    Schema for updating user information.

    All fields are optional to support partial updates (PATCH).
    Only provided fields will be updated.

    Note:
    - Password updates should use UserPasswordUpdateSchema
    - Role updates typically require admin privileges

    Attributes:
        username: New username (if changing)
        email: New email address (if changing)
        first_name: New first name (if changing)
        last_name: New last name (if changing)
        role: New role (admin only)

    Example:
        {
            "first_name": "Jane",
            "email": "jane@example.com"
        }
    """

    username: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=50,
        description="New username",
        json_schema_extra={"example": "janedoe"}
    )
    email: Optional[EmailStr] = Field(
        default=None,
        description="New email address",
        json_schema_extra={"example": "jane@example.com"}
    )
    first_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="New first name",
        json_schema_extra={"example": "Jane"}
    )
    last_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="New last name",
        json_schema_extra={"example": "Smith"}
    )
    role: Optional[UserRole] = Field(
        default=None,
        description="New role (admin only)"
    )

    @field_validator("username")
    @classmethod
    def check_username(cls, v: Optional[str]) -> Optional[str]:
        """Validate username if provided using utility validator."""
        return validate_username(v, allow_none=True)


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
        description="Current password (for verification)",
        json_schema_extra={"example": "OldPass123!"}
    )
    new_password: str = Field(
        min_length=8,
        max_length=255,
        description="New password (8-255 characters)",
        json_schema_extra={"example": "NewSecurePass456!"}
    )

    @field_validator("new_password")
    @classmethod
    def check_new_password(cls, v: str) -> str:
        """Validate new password strength using utility validator."""
        return validate_password(v, field_name="New password")


class UserResponseSchema(ResponseSchema):
    """
    Schema for user data in API responses.

    This schema inherits UUID and timestamps from ResponseSchema (BaseModelSchema).
    Password is never included in responses for security.

    Attributes:
        uuid: Unique identifier (inherited)
        username: User's username
        email: User's email address
        first_name: User's first name
        last_name: User's last name
        role: User's role
        full_name: Computed full name (first + last)
        created_at: When user registered (inherited)
        updated_at: When user was last updated (inherited)
        deleted_at: Soft delete timestamp (inherited)

    Example:
        {
            "uuid": "123e4567-e89b-12d3-a456-426614174000",
            "username": "johndoe",
            "email": "john@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "role": "USER",
            "full_name": "John Doe",
            "created_at": "2025-01-15T10:30:00Z",
            "updated_at": "2025-01-15T14:20:00Z",
            "deleted_at": null
        }
    """

    username: str = Field(
        description="User's username",
        json_schema_extra={"example": "johndoe"}
    )
    email: EmailStr = Field(
        description="User's email address",
        json_schema_extra={"example": "john@example.com"}
    )
    first_name: str = Field(
        description="User's first name",
        json_schema_extra={"example": "John"}
    )
    last_name: str = Field(
        description="User's last name",
        json_schema_extra={"example": "Doe"}
    )
    role: UserRole = Field(
        description="User's role"
    )

    @property
    def full_name(self) -> str:
        """
        Compute full name from first and last name.

        Returns:
            Full name as "First Last"
        """
        return f"{self.first_name} {self.last_name}"

    model_config = {
        "json_schema_extra": {
            "example": {
                "uuid": "123e4567-e89b-12d3-a456-426614174000",
                "username": "johndoe",
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "role": "USER",
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T14:20:00Z",
                "deleted_at": None
            }
        }
    }


class UserPublicSchema(ResponseSchema):
    """
    Schema for public user profile information.

    This is a limited version of UserResponseSchema that excludes
    sensitive information like email. Use this for public-facing endpoints
    or when showing user info to other users.

    Attributes:
        uuid: Unique identifier (inherited)
        username: User's username
        first_name: User's first name
        last_name: User's last name
        created_at: When user registered (inherited)

    Example:
        {
            "uuid": "123e4567-e89b-12d3-a456-426614174000",
            "username": "johndoe",
            "first_name": "John",
            "last_name": "Doe",
            "full_name": "John Doe",
            "created_at": "2025-01-15T10:30:00Z"
        }
    """

    username: str = Field(
        description="User's username",
        json_schema_extra={"example": "johndoe"}
    )
    first_name: str = Field(
        description="User's first name",
        json_schema_extra={"example": "John"}
    )
    last_name: str = Field(
        description="User's last name",
        json_schema_extra={"example": "Doe"}
    )

    @property
    def full_name(self) -> str:
        """Compute full name from first and last name."""
        return f"{self.first_name} {self.last_name}"
