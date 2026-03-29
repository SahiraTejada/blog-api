from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import (
    BaseSchema,
    CreateSchema,
    PaginatedResponse,
    PaginationMeta,
    PaginationParams,
    ResponseSchema,
    UpdateSchema,
)
from app.schemas.user import UserPublicSchema


class CommentCreateSchema(CreateSchema):
    """
    Schema for creating a new comment.

    Supports both top-level comments and replies.
    For a top-level comment, omit parent_comment_uuid.
    For a reply, provide the parent_comment_uuid.
    """

    content: str = Field(
        min_length=1,
        max_length=5000,
        description="Content of the comment",
        json_schema_extra={"example": "Great post! Very informative."},
    )
    post_uuid: UUID = Field(
        description="UUID of the post being commented on",
        json_schema_extra={"example": "123e4567-e89b-12d3-a456-426614174000"},
    )
    parent_comment_uuid: Optional[UUID] = Field(
        default=None,
        description="UUID of the parent comment (null for top-level comments)",
        json_schema_extra={"example": None},
    )


class CommentUpdateSchema(UpdateSchema):
    """
    Schema for updating an existing comment.

    Only the content can be updated.
    """

    content: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=5000,
        description="New content for the comment",
        json_schema_extra={"example": "Updated comment content."},
    )


class CommentResponse(ResponseSchema):
    """
    Schema for a single comment response.

    Includes author_uuid and post_uuid references,
    plus parent_comment_uuid for nested comments.
    """

    content: str = Field(
        description="Content of the comment",
        json_schema_extra={"example": "Great post! Very informative."},
    )
    post_uuid: UUID = Field(
        description="UUID of the post this comment belongs to",
        json_schema_extra={"example": "123e4567-e89b-12d3-a456-426614174000"},
    )
    author_uuid: UUID = Field(
        description="UUID of the comment author",
        json_schema_extra={"example": "223e4567-e89b-12d3-a456-426614174001"},
    )
    parent_comment_uuid: Optional[UUID] = Field(
        default=None,
        description="UUID of the parent comment (null for top-level comments)",
        json_schema_extra={"example": None},
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "uuid": "323e4567-e89b-12d3-a456-426614174002",
                "content": "Great post! Very informative.",
                "post_uuid": "123e4567-e89b-12d3-a456-426614174000",
                "author_uuid": "223e4567-e89b-12d3-a456-426614174001",
                "parent_comment_uuid": None,
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T10:30:00Z",
                "deleted_at": None,
            }
        }
    }


class CommentWithAuthorResponse(CommentResponse):
    """
    Schema for comment response including author information.

    Extends CommentResponse with full public author details.
    """

    author: UserPublicSchema = Field(
        description="Public information about the comment author",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "uuid": "323e4567-e89b-12d3-a456-426614174002",
                "content": "Great post! Very informative.",
                "post_uuid": "123e4567-e89b-12d3-a456-426614174000",
                "author_uuid": "223e4567-e89b-12d3-a456-426614174001",
                "parent_comment_uuid": None,
                "author": {
                    "uuid": "223e4567-e89b-12d3-a456-426614174001",
                    "username": "johndoe",
                    "first_name": "John",
                    "last_name": "Doe",
                },
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T10:30:00Z",
                "deleted_at": None,
            }
        }
    }


class CommentTreeNode(BaseSchema):
    """
    Schema for a comment node in a nested tree structure.

    Each node contains the comment data plus a list of reply nodes,
    supporting unlimited nesting depth.
    """

    comment: CommentWithAuthorResponse = Field(
        description="The comment data",
    )
    replies: List["CommentTreeNode"] = Field(
        default=[],
        description="List of reply nodes (recursive, unlimited depth)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "comment": {
                    "uuid": "323e4567-e89b-12d3-a456-426614174002",
                    "content": "Great post!",
                    "post_uuid": "123e4567-e89b-12d3-a456-426614174000",
                    "author_uuid": "223e4567-e89b-12d3-a456-426614174001",
                    "parent_comment_uuid": None,
                    "author": {
                        "uuid": "223e4567-e89b-12d3-a456-426614174001",
                        "username": "johndoe",
                        "first_name": "John",
                        "last_name": "Doe",
                    },
                    "created_at": "2025-01-15T10:30:00Z",
                    "updated_at": "2025-01-15T10:30:00Z",
                    "deleted_at": None,
                },
                "replies": [],
            }
        }
    }


class CommentListRequest(PaginationParams):
    """
    Request schema for listing comments with pagination and filters.
    """

    search_term: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Optional search term to filter comments by content",
        json_schema_extra={"example": "great"},
    )
    author_uuid: Optional[UUID] = Field(
        default=None,
        description="Filter comments by author UUID",
        json_schema_extra={"example": "223e4567-e89b-12d3-a456-426614174001"},
    )


class CommentListResponse(PaginatedResponse[CommentWithAuthorResponse]):
    """
    Schema for paginated list of comments.

    Used as response for list comments endpoints.
    """

    data: List[CommentWithAuthorResponse] = Field(
        description="List of comments for the current page",
    )
    pagination: PaginationMeta = Field(
        description="Pagination metadata",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "data": [
                    {
                        "uuid": "323e4567-e89b-12d3-a456-426614174002",
                        "content": "Great post! Very informative.",
                        "post_uuid": "123e4567-e89b-12d3-a456-426614174000",
                        "author_uuid": "223e4567-e89b-12d3-a456-426614174001",
                        "parent_comment_uuid": None,
                        "author": {
                            "uuid": "223e4567-e89b-12d3-a456-426614174001",
                            "username": "johndoe",
                            "first_name": "John",
                            "last_name": "Doe",
                        },
                        "created_at": "2025-01-15T10:30:00Z",
                        "updated_at": "2025-01-15T10:30:00Z",
                        "deleted_at": None,
                    }
                ],
                "pagination": {
                    "page": 1,
                    "page_size": 20,
                    "total_items": 50,
                    "total_pages": 3,
                    "has_next": True,
                    "has_previous": False,
                    "next_page": 2,
                    "previous_page": None,
                },
            }
        }
    }


class CommentCountResponse(BaseSchema):
    """
    Schema for comment count statistics.
    """

    post_uuid: UUID = Field(
        description="UUID of the post",
        json_schema_extra={"example": "123e4567-e89b-12d3-a456-426614174000"},
    )
    total_comments: int = Field(
        description="Total number of comments on the post",
        json_schema_extra={"example": 42},
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "post_uuid": "123e4567-e89b-12d3-a456-426614174000",
                "total_comments": 42,
            }
        }
    }
