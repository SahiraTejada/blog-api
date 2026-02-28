from typing import List, Optional

from pydantic import EmailStr, Field, field_validator

from app.models.users import UserRole
from app.schemas.base import PaginatedResponse, PaginationMeta, PaginationParams, ResponseSchema, UpdateSchema
from app.utils.validator_utils import validate_username


class UserBaseSchema(ResponseSchema):
    """
    Base schema for user information.

    This schema includes common user fields shared across different user schemas.
    It inherits UUID and timestamps from ResponseSchema (BaseModelSchema).

    Attributes:
        username: User's username
        first_name: User's first name
        last_name: User's last name
        role: User's role
    """

    username: str = Field(description="User's username", json_schema_extra={"example": "johndoe"})
    email: EmailStr = Field(description="User's email address", json_schema_extra={"example": "john@example.com"})
    first_name: str = Field(description="User's first name", json_schema_extra={"example": "John"})
    last_name: str = Field(description="User's last name", json_schema_extra={"example": "Doe"})
    role: UserRole = Field(description="User's role")

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
                "deleted_at": None,
            }
        }
    }


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
        default=None, min_length=3, max_length=50, description="New username", json_schema_extra={"example": "janedoe"}
    )
    email: Optional[EmailStr] = Field(
        default=None, description="New email address", json_schema_extra={"example": "jane@example.com"}
    )
    first_name: Optional[str] = Field(
        default=None, min_length=1, max_length=255, description="New first name", json_schema_extra={"example": "Jane"}
    )
    last_name: Optional[str] = Field(
        default=None, min_length=1, max_length=255, description="New last name", json_schema_extra={"example": "Smith"}
    )
    role: Optional[UserRole] = Field(default=None, description="New role (admin only)")

    @field_validator("username")
    @classmethod
    def check_username(cls, v: Optional[str]) -> Optional[str]:
        """Validate username if provided using utility validator."""
        return validate_username(v, allow_none=True)


class UserListRequest(PaginationParams):
    """
    Request schema for listing users with pagination and filters.
    """

    role: Optional[UserRole] = Field(
        default=None,
        description="Filter users by role",
    )
    search_term: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Search in username, email, first name, and last name",
        json_schema_extra={"example": "john"},
    )


class UserListResponse(PaginatedResponse[UserBaseSchema]):
    """
    Schema for paginated list of users.

    Used as response for list users endpoint.

    Attributes:
        data: List of users for the current page
        pagination: Pagination metadata (page, total_items, etc.)
    """

    data: List[UserBaseSchema] = Field(description="List of users for the current page")
    pagination: PaginationMeta = Field(description="Pagination metadata")


class UserPublicSchema(ResponseSchema):
    """
    Schema for public user profile information.

    This is a limited version of UserBaseSchema that excludes
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

    username: str = Field(description="User's username", json_schema_extra={"example": "johndoe"})
    first_name: str = Field(description="User's first name", json_schema_extra={"example": "John"})
    last_name: str = Field(description="User's last name", json_schema_extra={"example": "Doe"})

    @property
    def full_name(self) -> str:
        """Compute full name from first and last name."""
        return f"{self.first_name} {self.last_name}"
