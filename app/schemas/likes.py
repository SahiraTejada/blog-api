from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import Field

from app.schemas.base import (
    BaseSchema,
    PaginatedResponse,
    PaginationMeta,
    PaginationParams,
)
from app.schemas.user import UserPublicSchema


class LikeCreateSchema(BaseSchema):
    """
    Schema for creating a like.

    The user is inferred from the authenticated user's token,
    so only the post_uuid is required.
    """

    post_uuid: UUID = Field(
        description="UUID of the post to like",
        json_schema_extra={"example": "223e4567-e89b-12d3-a456-426614174001"},
    )


class LikeResponse(BaseSchema):
    """
    Schema for a like response.

    Includes both UUIDs and the creation timestamp.
    No uuid field since Like uses a composite primary key.
    """

    user_uuid: UUID = Field(
        description="UUID of the user who liked",
        json_schema_extra={"example": "123e4567-e89b-12d3-a456-426614174000"},
    )
    post_uuid: UUID = Field(
        description="UUID of the liked post",
        json_schema_extra={"example": "223e4567-e89b-12d3-a456-426614174001"},
    )
    created_at: datetime = Field(
        description="Timestamp when the like was created",
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "user_uuid": "123e4567-e89b-12d3-a456-426614174000",
                "post_uuid": "223e4567-e89b-12d3-a456-426614174001",
                "created_at": "2025-01-15T10:30:00Z",
            }
        }
    }


class LikeWithUserResponse(BaseSchema):
    """
    Schema for a like including the user's public info.

    Used in like lists to show who liked a post.
    """

    user_uuid: UUID = Field(
        description="UUID of the user who liked",
    )
    post_uuid: UUID = Field(
        description="UUID of the liked post",
    )
    created_at: datetime = Field(
        description="Timestamp when the like was created",
    )
    user: UserPublicSchema = Field(
        description="Public profile of the user who liked",
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "user_uuid": "123e4567-e89b-12d3-a456-426614174000",
                "post_uuid": "223e4567-e89b-12d3-a456-426614174001",
                "created_at": "2025-01-15T10:30:00Z",
                "user": {
                    "uuid": "123e4567-e89b-12d3-a456-426614174000",
                    "username": "johndoe",
                    "first_name": "John",
                    "last_name": "Doe",
                },
            }
        }
    }


class LikeStatusResponse(BaseSchema):
    """
    Schema for checking if a like exists.
    """

    has_liked: bool = Field(
        description="Whether the user has liked the post",
        json_schema_extra={"example": True},
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "has_liked": True,
            }
        }
    }


class LikeToggleResponse(BaseSchema):
    """
    Schema for the toggle like response.
    """

    liked: bool = Field(
        description="Whether the post is now liked (True) or unliked (False)",
        json_schema_extra={"example": True},
    )
    likes_count: int = Field(
        description="Updated total like count for the post",
        json_schema_extra={"example": 42},
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "liked": True,
                "likes_count": 42,
            }
        }
    }


class LikeCountResponse(BaseSchema):
    """
    Schema for like count statistics.
    """

    post_uuid: UUID = Field(
        description="UUID of the post",
        json_schema_extra={"example": "223e4567-e89b-12d3-a456-426614174001"},
    )
    likes_count: int = Field(
        description="Number of likes on the post",
        json_schema_extra={"example": 42},
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "post_uuid": "223e4567-e89b-12d3-a456-426614174001",
                "likes_count": 42,
            }
        }
    }


class LikeListRequest(PaginationParams):
    """
    Request schema for listing likes with pagination.
    """

    pass


class LikeListResponse(PaginatedResponse[LikeWithUserResponse]):
    """
    Schema for paginated list of likes.
    """

    data: List[LikeWithUserResponse] = Field(
        description="List of likes for the current page",
    )
    pagination: PaginationMeta = Field(
        description="Pagination metadata",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "data": [
                    {
                        "user_uuid": "123e4567-e89b-12d3-a456-426614174000",
                        "post_uuid": "223e4567-e89b-12d3-a456-426614174001",
                        "created_at": "2025-01-15T10:30:00Z",
                        "user": {
                            "uuid": "123e4567-e89b-12d3-a456-426614174000",
                            "username": "johndoe",
                            "first_name": "John",
                            "last_name": "Doe",
                        },
                    }
                ],
                "pagination": {
                    "page": 1,
                    "page_size": 20,
                    "total_items": 42,
                    "total_pages": 3,
                    "has_next": True,
                    "has_previous": False,
                    "next_page": 2,
                    "previous_page": None,
                },
            }
        }
    }
