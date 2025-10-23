"""
Base Schema Module

This module provides base Pydantic models that are reused across the application.
These schemas define common patterns for request/response models, reducing
code duplication and ensuring consistency.

Features:
- Base models with common fields (UUID, timestamps)
- Standard response formats (success, error)
- Reusable validation patterns
- Consistent serialization configuration

Author: Blog API Team
Date: 2025-10-20
"""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# TYPE VARIABLES
# ============================================================================

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

    Configuration:
    - from_attributes: Allows creating instances from ORM models
    - populate_by_name: Allows field population by both alias and name
    - json_schema_extra: Additional metadata for OpenAPI docs
    """

    model_config = ConfigDict(
        from_attributes=True,  # Enable ORM mode (was orm_mode in Pydantic v1)
        populate_by_name=True,  # Allow using field names or aliases
        str_strip_whitespace=True,  # Strip whitespace from strings
        use_enum_values=True,  # Use enum values instead of enum objects
    )


class TimestampSchema(BaseSchema):
    """
    Schema with timestamp fields.

    Use this as a base for any model that includes creation/update timestamps.
    This is typically used for response models that mirror database models.

    Attributes:
        created_at: When the record was created
        updated_at: When the record was last updated
        deleted_at: When the record was soft-deleted (None if not deleted)

    Example:
        class UserResponse(TimestampSchema):
            uuid: UUID
            email: str
            name: str
            # Inherits created_at, updated_at, deleted_at
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

    Attributes:
        uuid: Unique identifier for the record

    Example:
        class CategoryResponse(UUIDSchema):
            name: str
            slug: str
            # Inherits uuid
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

    Attributes:
        uuid: Unique identifier
        created_at: Creation timestamp
        updated_at: Last update timestamp
        deleted_at: Soft delete timestamp

    Example:
        class PostResponse(BaseModelSchema):
            title: str
            content: str
            author_id: UUID
            # Inherits uuid, created_at, updated_at, deleted_at
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

class IDListSchema(BaseSchema):
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

    ids: List[UUID] = Field(
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


# ============================================================================
# USAGE EXAMPLES
# ============================================================================
"""
USAGE EXAMPLES IN YOUR MODELS:

# 1. Creating a response model
from app.schemas.base import ResponseSchema

class UserResponse(ResponseSchema):
    email: str
    name: str
    is_active: bool
    # Automatically inherits: uuid, created_at, updated_at, deleted_at


# 2. Creating a create schema
from app.schemas.base import CreateSchema
from pydantic import EmailStr

class UserCreate(CreateSchema):
    email: EmailStr
    name: str
    password: str
    # No UUID or timestamps - those are generated


# 3. Creating an update schema
from app.schemas.base import UpdateSchema

class UserUpdate(UpdateSchema):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    # All fields optional for partial updates


# 4. Using in FastAPI routes
from fastapi import APIRouter, HTTPException
from app.schemas.base import SuccessResponse, MessageResponse

router = APIRouter()

@router.delete("/users/{user_id}", response_model=SuccessResponse)
def delete_user(user_id: UUID, db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    deleted = user_repo.delete(user_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")

    return SuccessResponse(
        message="User deleted successfully",
        data={"user_id": str(user_id)}
    )


@router.post("/users/bulk", response_model=BulkOperationResponse)
def bulk_create_users(
    users: List[UserCreate],
    db: Session = Depends(get_db)
):
    user_repo = UserRepository(db)
    succeeded = 0
    failed = 0
    errors = []

    for user_data in users:
        try:
            user_repo.create(user_data.model_dump())
            succeeded += 1
        except Exception as e:
            failed += 1
            errors.append(ErrorDetail(
                message=str(e),
                code="CREATE_FAILED"
            ))

    return BulkOperationResponse(
        success=failed == 0,
        message=f"Created {succeeded} users",
        total=len(users),
        succeeded=succeeded,
        failed=failed,
        errors=errors if errors else None
    )


# 5. Custom error responses
from fastapi import Request
from fastapi.responses import JSONResponse
from app.schemas.base import ErrorResponse, ErrorDetail

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            message="Invalid input",
            errors=[ErrorDetail(message=str(exc), code="INVALID_VALUE")],
            status_code=400
        ).model_dump()
    )
"""
