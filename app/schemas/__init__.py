"""
Schemas Package

This module exports all Pydantic schemas for API request/response validation.
"""

# Base schemas
from app.schemas.base import (
    BaseModelSchema,
    BaseSchema,
    BulkOperationResponse,
    CreateSchema,
    DataResponse,
    ErrorDetail,
    ErrorResponse,
    MessageResponse,
    PaginatedResponse,
    PaginationMeta,
    PaginationParams,
    ResponseSchema,
    StatusSchema,
    SuccessResponse,
    TimestampSchema,
    UpdateSchema,
    UUIDListSchema,
    UUIDSchema,
)

# User schemas
from app.schemas.user import (
    UserPublicSchema,
    UserBaseSchema,
    UserResponseSchema,
    UserUpdateSchema,
)

__all__ = [
    # Base schemas
    "BaseSchema",
    "BaseModelSchema",
    "CreateSchema",
    "UpdateSchema",
    "ResponseSchema",
    "TimestampSchema",
    "UUIDSchema",
    "PaginationParams",
    "PaginationMeta",
    "PaginatedResponse",
    "SuccessResponse",
    "ErrorDetail",
    "ErrorResponse",
    "MessageResponse",
    "DataResponse",
    "BulkOperationResponse",
    "StatusSchema",
    "UUIDListSchema",
    # User schemas
    "UserUpdateSchema",
    "UserResponseSchema",
    "UserPublicSchema",
    "UserBaseSchema"
]
