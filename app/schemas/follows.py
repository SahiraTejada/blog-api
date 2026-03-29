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


class FollowCreateSchema(BaseSchema):
    """
    Schema for creating a follow relationship.

    The follower is inferred from the authenticated user's token,
    so only the followee_uuid is required.
    """

    followee_uuid: UUID = Field(
        description="UUID of the user to follow",
        json_schema_extra={"example": "223e4567-e89b-12d3-a456-426614174001"},
    )


class FollowResponse(BaseSchema):
    """
    Schema for a follow relationship response.

    Includes both UUIDs and the creation timestamp.
    No uuid field since Follow uses a composite primary key.
    """

    follower_uuid: UUID = Field(
        description="UUID of the follower",
        json_schema_extra={"example": "123e4567-e89b-12d3-a456-426614174000"},
    )
    followee_uuid: UUID = Field(
        description="UUID of the user being followed",
        json_schema_extra={"example": "223e4567-e89b-12d3-a456-426614174001"},
    )
    created_at: datetime = Field(
        description="Timestamp when the follow was created",
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "follower_uuid": "123e4567-e89b-12d3-a456-426614174000",
                "followee_uuid": "223e4567-e89b-12d3-a456-426614174001",
                "created_at": "2025-01-15T10:30:00Z",
            }
        }
    }


class FollowWithUserResponse(BaseSchema):
    """
    Schema for a follow relationship including the related user's public info.

    Used in follower/following lists to show who the user is.
    """

    follower_uuid: UUID = Field(
        description="UUID of the follower",
    )
    followee_uuid: UUID = Field(
        description="UUID of the user being followed",
    )
    created_at: datetime = Field(
        description="Timestamp when the follow was created",
    )
    user: UserPublicSchema = Field(
        description="Public profile of the related user (follower or followee)",
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "follower_uuid": "123e4567-e89b-12d3-a456-426614174000",
                "followee_uuid": "223e4567-e89b-12d3-a456-426614174001",
                "created_at": "2025-01-15T10:30:00Z",
                "user": {
                    "uuid": "223e4567-e89b-12d3-a456-426614174001",
                    "username": "janedoe",
                    "first_name": "Jane",
                    "last_name": "Doe",
                },
            }
        }
    }


class FollowStatusResponse(BaseSchema):
    """
    Schema for checking if a follow relationship exists.
    """

    is_following: bool = Field(
        description="Whether the user is following the target user",
        json_schema_extra={"example": True},
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "is_following": True,
            }
        }
    }


class FollowCountResponse(BaseSchema):
    """
    Schema for follower/following count statistics.
    """

    user_uuid: UUID = Field(
        description="UUID of the user",
        json_schema_extra={"example": "123e4567-e89b-12d3-a456-426614174000"},
    )
    followers_count: int = Field(
        description="Number of followers",
        json_schema_extra={"example": 150},
    )
    following_count: int = Field(
        description="Number of users being followed",
        json_schema_extra={"example": 75},
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_uuid": "123e4567-e89b-12d3-a456-426614174000",
                "followers_count": 150,
                "following_count": 75,
            }
        }
    }


class FollowListRequest(PaginationParams):
    """
    Request schema for listing followers/following with pagination.
    """

    pass


class FollowListResponse(PaginatedResponse[FollowWithUserResponse]):
    """
    Schema for paginated list of follow relationships.

    Used for both followers and following endpoints.
    """

    data: List[FollowWithUserResponse] = Field(
        description="List of follow relationships for the current page",
    )
    pagination: PaginationMeta = Field(
        description="Pagination metadata",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "data": [
                    {
                        "follower_uuid": "123e4567-e89b-12d3-a456-426614174000",
                        "followee_uuid": "223e4567-e89b-12d3-a456-426614174001",
                        "created_at": "2025-01-15T10:30:00Z",
                        "user": {
                            "uuid": "223e4567-e89b-12d3-a456-426614174001",
                            "username": "janedoe",
                            "first_name": "Jane",
                            "last_name": "Doe",
                        },
                    }
                ],
                "pagination": {
                    "page": 1,
                    "page_size": 20,
                    "total_items": 150,
                    "total_pages": 8,
                    "has_next": True,
                    "has_previous": False,
                    "next_page": 2,
                    "previous_page": None,
                },
            }
        }
    }
