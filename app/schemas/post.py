from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.models.posts import PostStatus
from app.schemas.base import (
    BaseSchema,
    CreateSchema,
    PaginatedResponse,
    PaginationMeta,
    PaginationParams,
    ResponseSchema,
    UpdateSchema,
)
from app.schemas.category import CategoryResponse
from app.schemas.user import UserPublicSchema


class PostBaseSchema(BaseSchema):
    """
    Base schema with common post fields.

    Defines the core fields and validations shared across post schemas.
    """

    title: str = Field(
        min_length=1,
        max_length=255,
        description="Title of the post",
        json_schema_extra={"example": "Introduction to FastAPI"},
    )
    content: str = Field(
        min_length=1,
        description="Content of the post",
        json_schema_extra={"example": "This is the content of the blog post."},
    )
    status: PostStatus = Field(
        default=PostStatus.DRAFT,
        description="Publication status of the post",
        json_schema_extra={"example": "DRAFT"},
    )


class PostCreateSchema(CreateSchema):
    """
    Schema for creating a new post.

    Includes required fields for post creation plus optional category assignment.
    """

    title: str = Field(
        min_length=1,
        max_length=255,
        description="Title of the post",
        json_schema_extra={"example": "Introduction to FastAPI"},
    )
    content: str = Field(
        min_length=1,
        description="Content of the post",
        json_schema_extra={"example": "This is the content of the blog post."},
    )
    status: PostStatus = Field(
        default=PostStatus.DRAFT,
        description="Publication status of the post",
        json_schema_extra={"example": "DRAFT"},
    )
    category_uuids: Optional[List[UUID]] = Field(
        default=None,
        description="List of category UUIDs to assign to the post",
        json_schema_extra={"example": ["123e4567-e89b-12d3-a456-426614174000"]},
    )


class PostUpdateSchema(UpdateSchema):
    """
    Schema for updating an existing post.

    All fields are optional to support partial updates (PATCH).
    Only provided fields will be updated.
    """

    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="New title for the post",
        json_schema_extra={"example": "Updated: Introduction to FastAPI"},
    )
    content: Optional[str] = Field(
        default=None,
        min_length=1,
        description="New content for the post",
        json_schema_extra={"example": "This is the updated content of the blog post."},
    )
    status: Optional[PostStatus] = Field(
        default=None,
        description="New publication status",
        json_schema_extra={"example": "PUBLISHED"},
    )
    category_uuids: Optional[List[UUID]] = Field(
        default=None,
        description="New list of category UUIDs (replaces existing categories)",
        json_schema_extra={"example": ["123e4567-e89b-12d3-a456-426614174000"]},
    )


class PostResponse(PostBaseSchema, ResponseSchema):
    """
    Schema for post response.

    Combines PostBaseSchema fields with ResponseSchema (UUID + timestamps).

    Attributes:
        uuid: Unique identifier (from ResponseSchema)
        title: Post title (from PostBaseSchema)
        content: Post content (from PostBaseSchema)
        status: Publication status (from PostBaseSchema)
        author_uuid: UUID of the post author
        categories: List of categories assigned to the post
        created_at, updated_at, deleted_at: Timestamps (from ResponseSchema)
    """

    author_uuid: UUID = Field(
        description="Unique identifier (UUID) of the post author",
        json_schema_extra={"example": "123e4567-e89b-12d3-a456-426614174000"},
    )
    categories: List[CategoryResponse] = Field(
        default=[],
        description="List of categories assigned to the post",
    )
    likes_count: int = Field(
        default=0,
        description="Number of active likes on the post",
        json_schema_extra={"example": 42},
    )
    comments_count: int = Field(
        default=0,
        description="Number of active comments on the post",
        json_schema_extra={"example": 15},
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "uuid": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Introduction to FastAPI",
                "content": "This is the content of the blog post.",
                "status": "PUBLISHED",
                "author_uuid": "223e4567-e89b-12d3-a456-426614174001",
                "categories": [
                    {
                        "uuid": "323e4567-e89b-12d3-a456-426614174002",
                        "name": "Technology",
                        "description": "Posts about technology",
                        "created_at": "2025-01-15T10:30:00Z",
                        "updated_at": "2025-01-15T10:30:00Z",
                        "deleted_at": None,
                    }
                ],
                "likes_count": 42,
                "comments_count": 15,
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T14:20:00Z",
                "deleted_at": None,
            }
        }
    }


class PostWithAuthorResponse(PostResponse):
    """
    Schema for post response including author information.

    Extends PostResponse with full author details.
    """

    author: UserPublicSchema = Field(
        description="Public information about the post author",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "uuid": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Introduction to FastAPI",
                "content": "This is the content of the blog post.",
                "status": "PUBLISHED",
                "author_uuid": "223e4567-e89b-12d3-a456-426614174001",
                "author": {
                    "uuid": "223e4567-e89b-12d3-a456-426614174001",
                    "username": "johndoe",
                    "first_name": "John",
                    "last_name": "Doe",
                },
                "categories": [],
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T14:20:00Z",
                "deleted_at": None,
            }
        }
    }


class PostListRequest(PaginationParams):
    """
    Request schema for listing posts with pagination and filters.
    """

    search_term: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Optional search term to filter posts by title or content",
        json_schema_extra={"example": "FastAPI"},
    )
    author_uuid: Optional[UUID] = Field(
        default=None,
        description="Filter posts by author UUID",
        json_schema_extra={"example": "123e4567-e89b-12d3-a456-426614174000"},
    )
    category_uuid: Optional[UUID] = Field(
        default=None,
        description="Filter posts by category UUID",
        json_schema_extra={"example": "123e4567-e89b-12d3-a456-426614174000"},
    )
    status: Optional[PostStatus] = Field(
        default=None,
        description="Filter posts by publication status",
        json_schema_extra={"example": "PUBLISHED"},
    )


class PostListResponse(PaginatedResponse[PostResponse]):
    """
    Schema for paginated list of posts.

    Used as response for list posts endpoint.

    Attributes:
        data: List of posts for the current page
        pagination: Pagination metadata (page, total_items, etc.)
    """

    data: List[PostResponse] = Field(description="List of posts for the current page")
    pagination: PaginationMeta = Field(description="Pagination metadata")

    model_config = {
        "json_schema_extra": {
            "example": {
                "data": [
                    {
                        "uuid": "123e4567-e89b-12d3-a456-426614174000",
                        "title": "Introduction to FastAPI",
                        "content": "This is the content of the blog post.",
                        "status": "PUBLISHED",
                        "author_uuid": "223e4567-e89b-12d3-a456-426614174001",
                        "categories": [],
                        "created_at": "2025-01-15T10:30:00Z",
                        "updated_at": "2025-01-15T14:20:00Z",
                        "deleted_at": None,
                    },
                    {
                        "uuid": "223e4567-e89b-12d3-a456-426614174001",
                        "title": "Advanced Python Tips",
                        "content": "Python tips and tricks for advanced users.",
                        "status": "DRAFT",
                        "author_uuid": "223e4567-e89b-12d3-a456-426614174001",
                        "categories": [],
                        "created_at": "2025-01-16T08:00:00Z",
                        "updated_at": "2025-01-16T08:00:00Z",
                        "deleted_at": None,
                    },
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


class PostStatusCountResponse(BaseSchema):
    """
    Schema for post count by status.

    Used when returning statistics about posts.
    """

    status: PostStatus = Field(
        description="Publication status of the post",
        json_schema_extra={"example": "PUBLISHED"},
    )
    post_count: int = Field(
        description="Number of posts with this status",
        json_schema_extra={"example": 42},
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "PUBLISHED",
                "post_count": 42,
            }
        }
    }
