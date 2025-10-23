from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")
# Generic type variable for flexible response models


# ============================================================================
# BASE REQUEST/RESPONSE MODELS
# ============================================================================

class BaseSchema(BaseModel):
    """
    Base schema with common Pydantic configuration.

    All schema classes should inherit from this to ensure consistent
    behavior across the application.
    """

    model_config = ConfigDict(
        from_attributes=True,  # Enable ORM mode (was orm_mode in Pydantic v1)
        str_strip_whitespace=True,  # Strip whitespace from strings
        use_enum_values=True,  # Use enum values instead of enum objects
    )


class TimestampSchema(BaseSchema):
    """
    Schema with timestamp fields.

    Use this as a base for any model that includes creation/update timestamps.
    This is typically used for response models that mirror database models.
    """

    created_at: datetime = Field(
        description="Timestamp when the record was created"
    )
    updated_at: datetime = Field(
        description="Timestamp when the record was last updated"
    )
    deleted_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the record was soft-deleted (null if active)"
    )


class UUIDSchema(BaseSchema):
    """
    Schema with UUID primary key.

    Use this for response models that include a UUID identifier.
    """

    uuid: UUID = Field(
        description="Unique identifier (UUID) for the record"
    )


class BaseModelSchema(UUIDSchema, TimestampSchema):
    """
    Complete base schema with UUID and timestamps.

    This combines UUIDSchema and TimestampSchema to provide all common
    fields that database models have. Use this as the base for most
    response models.
    """

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "uuid": "123e4567-e89b-12d3-a456-426614174000",
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T14:20:00Z",
                "deleted_at": None
            }
        }
    )


class PaginationParams(BaseModel):
    """
    Standard pagination parameters for API endpoints.

    This class defines the common query parameters used for pagination
    across all endpoints. Use it with FastAPI's Depends() to automatically
    validate and parse pagination parameters.

    Attributes:
        page: Current page number (1-indexed)
        page_size: Number of items per page
        skip: Number of items to skip (calculated automatically)

    Example usage in FastAPI:
        @router.get("/users")
        def get_users(
            pagination: PaginationParams = Depends(),
            db: Session = Depends(get_db)
        ):
            users = user_repo.get_multi(
                skip=pagination.skip,
                limit=pagination.page_size
            )
            return paginate(users, pagination, total_count)
    """

    page: int = Field(
        default=1,
        ge=1,
        description="Page number (1-indexed). Must be at least 1."
    )
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of items per page. Must be between 1 and 100."
    )

    @property
    def skip(self) -> int:
        """
        Calculate the number of items to skip for the current page.

        This converts page-based pagination to offset-based pagination
        for database queries.

        Returns:
            Number of items to skip

        Example:
            page=1, page_size=20 -> skip=0
            page=2, page_size=20 -> skip=20
            page=3, page_size=20 -> skip=40
        """
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """
        Get the page size (alias for consistency with repository methods).

        Returns:
            Number of items per page
        """
        return self.page_size

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "page": 1,
                "page_size": 20
            }
        }


class PaginationMeta(BaseModel):
    """
    Metadata about the paginated response.

    This provides clients with all the information they need to:
    - Display current page information
    - Calculate total pages
    - Navigate to other pages
    - Show "showing X to Y of Z items"

    Attributes:
        page: Current page number
        page_size: Items per page
        total_items: Total number of items across all pages
        total_pages: Total number of pages
        has_next: Whether there is a next page
        has_previous: Whether there is a previous page
        next_page: Next page number (None if no next page)
        previous_page: Previous page number (None if no previous page)
    """

    page: int = Field(description="Current page number (1-indexed)")
    page_size: int = Field(description="Number of items per page")
    total_items: int = Field(description="Total number of items")
    total_pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_previous: bool = Field(description="Whether there is a previous page")
    next_page: Optional[int] = Field(
        default=None,
        description="Next page number (null if no next page)"
    )
    previous_page: Optional[int] = Field(
        default=None,
        description="Previous page number (null if no previous page)"
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "page": 2,
                "page_size": 20,
                "total_items": 150,
                "total_pages": 8,
                "has_next": True,
                "has_previous": True,
                "next_page": 3,
                "previous_page": 1
            }
        }


# ============================================================================
# CRUD SCHEMAS
# ============================================================================

class CreateSchema(BaseSchema):
    """
    Base schema for create (POST) requests.

    Use this as the base for schemas that represent data needed
    to create a new resource. It excludes fields like UUID and
    timestamps that are generated automatically.

    Example:
        class UserCreate(CreateSchema):
            email: EmailStr
            name: str
            password: str
            # UUID and timestamps will be generated automatically
    """

    pass


class UpdateSchema(BaseSchema):
    """
    Base schema for update (PUT/PATCH) requests.

    Use this for schemas that represent data for updating existing resources.
    Typically, all fields are optional to support partial updates (PATCH).

    Example:
        class UserUpdate(UpdateSchema):
            email: Optional[EmailStr] = None
            name: Optional[str] = None
            # Only provided fields will be updated
    """

    pass


class ResponseSchema(BaseModelSchema):
    """
    Base schema for response models.

    This is an alias for BaseModelSchema with a more explicit name.
    Use this as the base for API response models.

    Example:
        class CommentResponse(ResponseSchema):
            content: str
            post_id: UUID
            author_id: UUID
            # Inherits uuid, timestamps
    """

    pass


# ============================================================================
# STANDARD API RESPONSES
# ============================================================================

class SuccessResponse(BaseSchema):
    """
    Standard success response format.

    Use this for operations that don't return specific data,
    like successful deletions or void operations.

    Attributes:
        success: Always True for success responses
        message: Human-readable success message
        data: Optional additional data

    Example response:
        {
            "success": true,
            "message": "User deleted successfully",
            "data": null
        }
    """

    success: bool = Field(
        default=True,
        description="Indicates the operation was successful"
    )
    message: str = Field(
        description="Human-readable success message"
    )
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional additional data"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": None
            }
        }
    )


class ErrorDetail(BaseSchema):
    """
    Detailed error information.

    Attributes:
        field: The field that caused the error (for validation errors)
        message: Error message
        code: Error code for programmatic handling

    Example:
        {
            "field": "email",
            "message": "Email address is already registered",
            "code": "EMAIL_ALREADY_EXISTS"
        }
    """

    field: Optional[str] = Field(
        default=None,
        description="Field name that caused the error (for validation errors)"
    )
    message: str = Field(
        description="Human-readable error message"
    )
    code: Optional[str] = Field(
        default=None,
        description="Error code for programmatic handling"
    )


class ErrorResponse(BaseSchema):
    """
    Standard error response format.

    Use this for error responses to maintain consistency.
    FastAPI can automatically use this with exception handlers.

    Attributes:
        success: Always False for error responses
        message: Main error message
        errors: List of detailed error information
        status_code: HTTP status code

    Example response:
        {
            "success": false,
            "message": "Validation failed",
            "errors": [
                {
                    "field": "email",
                    "message": "Invalid email format",
                    "code": "INVALID_EMAIL"
                }
            ],
            "status_code": 422
        }
    """

    success: bool = Field(
        default=False,
        description="Always false for error responses"
    )
    message: str = Field(
        description="Main error message"
    )
    errors: Optional[List[ErrorDetail]] = Field(
        default=None,
        description="Detailed error information"
    )
    status_code: int = Field(
        description="HTTP status code"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "message": "Validation error",
                "errors": [
                    {
                        "field": "email",
                        "message": "Email is required",
                        "code": "REQUIRED_FIELD"
                    }
                ],
                "status_code": 422
            }
        }
    )


class MessageResponse(BaseSchema):
    """
    Simple message response.

    Use this for endpoints that only need to return a message,
    like confirmations or acknowledgments.

    Attributes:
        message: The message to return

    Example:
        {
            "message": "Password reset email sent"
        }
    """

    message: str = Field(
        description="Response message"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Operation completed successfully"
            }
        }
    )


class DataResponse(BaseSchema, Generic[T]):
    """
    Generic data wrapper response.

    Use this when you want to wrap data in a consistent envelope format.
    This is useful when you need to include metadata alongside the data.

    Type Parameters:
        T: The type of data being returned

    Attributes:
        data: The actual data payload
        meta: Optional metadata about the response

    Example:
        {
            "data": {
                "uuid": "...",
                "name": "John Doe"
            },
            "meta": {
                "version": "1.0",
                "timestamp": "2025-01-15T10:30:00Z"
            }
        }
    """

    data: T = Field(
        description="The response data payload"
    )
    meta: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata about the response"
    )


class BulkOperationResponse(BaseSchema):
    """
    Response for bulk operations.

    Use this for endpoints that perform operations on multiple items,
    like bulk create, update, or delete.

    Attributes:
        success: Whether the overall operation succeeded
        message: Summary message
        total: Total number of items processed
        succeeded: Number of items that succeeded
        failed: Number of items that failed
        errors: List of errors for failed items

    Example:
        {
            "success": true,
            "message": "Bulk operation completed",
            "total": 100,
            "succeeded": 95,
            "failed": 5,
            "errors": [
                {
                    "field": "items[3]",
                    "message": "Item already exists",
                    "code": "DUPLICATE"
                }
            ]
        }
    """

    success: bool = Field(
        description="Whether the operation succeeded overall"
    )
    message: str = Field(
        description="Summary message"
    )
    total: int = Field(
        description="Total number of items processed"
    )
    succeeded: int = Field(
        description="Number of items that succeeded"
    )
    failed: int = Field(
        description="Number of items that failed"
    )
    errors: Optional[List[ErrorDetail]] = Field(
        default=None,
        description="Errors for failed items"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Bulk create completed",
                "total": 100,
                "succeeded": 95,
                "failed": 5,
                "errors": []
            }
        }
    )


# ============================================================================
# VALIDATION SCHEMAS
# ============================================================================

class UUIDListSchema(BaseSchema):
    """
    Schema for requests with a list of IDs.

    Use this for bulk operations that accept multiple IDs.

    Attributes:
        ids: List of UUIDs

    Example request:
        {
            "ids": [
                "123e4567-e89b-12d3-a456-426614174000",
                "123e4567-e89b-12d3-a456-426614174001"
            ]
        }
    """

    uuids: List[UUID] = Field(
        min_length=1,
        description="List of UUIDs (at least one required)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ids": [
                    "123e4567-e89b-12d3-a456-426614174000",
                    "123e4567-e89b-12d3-a456-426614174001"
                ]
            }
        }
    )


class PaginatedResponse(BaseSchema, Generic[T]):
    """
    Generic paginated response wrapper.

    Use this for endpoints that return paginated lists of items.
    It provides both the data and pagination metadata in a consistent format.

    Type Parameters:
        T: The type of items in the data list

    Attributes:
        data: List of items for the current page
        pagination: Pagination metadata

    Example response:
        {
            "data": [
                {"uuid": "...", "name": "Item 1"},
                {"uuid": "...", "name": "Item 2"}
            ],
            "pagination": {
                "page": 1,
                "page_size": 20,
                "total_items": 50,
                "total_pages": 3,
                "has_next": true,
                "has_previous": false,
                "next_page": 2,
                "previous_page": null
            }
        }
    """

    data: List[T] = Field(
        description="List of items for the current page"
    )
    pagination: PaginationMeta = Field(
        description="Pagination metadata"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": [],
                "pagination": {
                    "page": 1,
                    "page_size": 20,
                    "total_items": 50,
                    "total_pages": 3,
                    "has_next": True,
                    "has_previous": False,
                    "next_page": 2,
                    "previous_page": None
                }
            }
        }
    )


class StatusSchema(BaseSchema):
    """
    Schema for status information.

    Use this for health checks or status endpoints.

    Attributes:
        status: Status indicator (healthy, degraded, unhealthy)
        message: Additional status information
        timestamp: When the status was checked
        details: Optional detailed status information

    Example:
        {
            "status": "healthy",
            "message": "All systems operational",
            "timestamp": "2025-01-15T10:30:00Z",
            "details": {
                "database": "connected",
                "cache": "connected"
            }
        }
    """

    status: str = Field(
        description="Status indicator"
    )
    message: str = Field(
        description="Status message"
    )
    timestamp: datetime = Field(
        description="When the status was checked"
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Detailed status information"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "message": "All systems operational",
                "timestamp": "2025-01-15T10:30:00Z",
                "details": {
                    "database": "connected"
                }
            }
        }
    )
