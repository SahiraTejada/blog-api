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

# Comment schemas
from app.schemas.comment import (
    CommentCountResponse,
    CommentCreateSchema,
    CommentListRequest,
    CommentListResponse,
    CommentResponse,
    CommentTreeNode,
    CommentUpdateSchema,
    CommentWithAuthorResponse,
)

# User schemas
from app.schemas.user import (
    UserBaseSchema,
    UserListRequest,
    UserListResponse,
    UserPublicSchema,
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
    # Comment schemas
    "CommentCreateSchema",
    "CommentUpdateSchema",
    "CommentResponse",
    "CommentWithAuthorResponse",
    "CommentTreeNode",
    "CommentListRequest",
    "CommentListResponse",
    "CommentCountResponse",
    # User schemas
    "UserUpdateSchema",
    "UserListRequest",
    "UserListResponse",
    "UserPublicSchema",
    "UserBaseSchema"
]
