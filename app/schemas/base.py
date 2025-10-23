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
