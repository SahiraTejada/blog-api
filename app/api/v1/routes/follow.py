"""
Follow Routes Module

This module provides API endpoints for follow management operations including:
- Follow a user (authenticated)
- Unfollow a user (authenticated)
- Check if following a user (authenticated)
- List followers of a user (public, paginated)
- List following of a user (public, paginated)
- Get follower/following counts (public)

All endpoints follow REST conventions and return standardized responses.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import AuthContext, require_user
from app.database.session import get_db
from app.schemas.base import SuccessResponse
from app.schemas.follows import (
    FollowCountResponse,
    FollowCreateSchema,
    FollowListRequest,
    FollowListResponse,
    FollowResponse,
    FollowStatusResponse,
    FollowWithUserResponse,
)
from app.services.follows_service import FollowService

router = APIRouter(prefix="/follow", tags=["Follow"])


# ============================================================================
# FOLLOW / UNFOLLOW
# ============================================================================


@router.post(
    "/",
    response_model=FollowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Follow a user",
    responses={
        201: {"description": "Successfully followed the user"},
        400: {"description": "Cannot follow yourself"},
        401: {"description": "Invalid or missing token"},
        404: {"description": "User not found"},
        409: {"description": "Already following this user"},
    },
)
async def follow_user(
    data: FollowCreateSchema,
    auth: AuthContext = Depends(require_user),
    db: Session = Depends(get_db),
) -> FollowResponse:
    """
    Follow a user.

    Requires authentication. The follower is the authenticated user.

    - **followee_uuid**: UUID of the user to follow
    """
    follow_service = FollowService(db)

    follow = follow_service.follow(
        follower_uuid=auth.user.uuid,
        followee_uuid=data.followee_uuid,
    )

    return FollowResponse.model_validate(follow)


@router.delete(
    "/{followee_uuid}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Unfollow a user",
    responses={
        200: {"description": "Successfully unfollowed the user"},
        401: {"description": "Invalid or missing token"},
        404: {"description": "Follow relationship not found"},
    },
)
async def unfollow_user(
    followee_uuid: UUID,
    auth: AuthContext = Depends(require_user),
    db: Session = Depends(get_db),
) -> SuccessResponse:
    """
    Unfollow a user.

    Requires authentication. The follower is the authenticated user.
    """
    follow_service = FollowService(db)

    follow_service.unfollow(
        follower_uuid=auth.user.uuid,
        followee_uuid=followee_uuid,
    )

    return SuccessResponse(message="Successfully unfollowed the user")


# ============================================================================
# FOLLOW STATUS
# ============================================================================


@router.get(
    "/status/{target_uuid}",
    response_model=FollowStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Check if following a user",
    responses={
        200: {"description": "Follow status"},
        401: {"description": "Invalid or missing token"},
    },
)
async def check_follow_status(
    target_uuid: UUID,
    auth: AuthContext = Depends(require_user),
    db: Session = Depends(get_db),
) -> FollowStatusResponse:
    """
    Check if the authenticated user is following a target user.

    Requires authentication.
    """
    follow_service = FollowService(db)

    is_following = follow_service.is_following(
        follower_uuid=auth.user.uuid,
        followee_uuid=target_uuid,
    )

    return FollowStatusResponse(is_following=is_following)


# ============================================================================
# FOLLOWERS & FOLLOWING LISTS
# ============================================================================


@router.get(
    "/{user_uuid}/followers",
    response_model=FollowListResponse,
    status_code=status.HTTP_200_OK,
    summary="List followers of a user",
    responses={
        200: {"description": "Paginated list of followers"},
        404: {"description": "User not found"},
    },
)
async def list_followers(
    user_uuid: UUID,
    pagination: FollowListRequest = Depends(),
    db: Session = Depends(get_db),
) -> FollowListResponse:
    """
    List all followers of a user with pagination.

    Public endpoint. No authentication required.
    """
    follow_service = FollowService(db)

    result = follow_service.get_followers(
        user_uuid=user_uuid,
        pagination=pagination,
    )

    return FollowListResponse(
        data=[
            FollowWithUserResponse(
                follower_uuid=f.follower_uuid,
                followee_uuid=f.followee_uuid,
                created_at=f.created_at,
                user=f.follower,
            )
            for f in result.data
        ],
        pagination=result.pagination,
    )


@router.get(
    "/{user_uuid}/following",
    response_model=FollowListResponse,
    status_code=status.HTTP_200_OK,
    summary="List users that a user is following",
    responses={
        200: {"description": "Paginated list of following"},
        404: {"description": "User not found"},
    },
)
async def list_following(
    user_uuid: UUID,
    pagination: FollowListRequest = Depends(),
    db: Session = Depends(get_db),
) -> FollowListResponse:
    """
    List all users that a user is following with pagination.

    Public endpoint. No authentication required.
    """
    follow_service = FollowService(db)

    result = follow_service.get_following(
        user_uuid=user_uuid,
        pagination=pagination,
    )

    return FollowListResponse(
        data=[
            FollowWithUserResponse(
                follower_uuid=f.follower_uuid,
                followee_uuid=f.followee_uuid,
                created_at=f.created_at,
                user=f.followee,
            )
            for f in result.data
        ],
        pagination=result.pagination,
    )


# ============================================================================
# STATISTICS
# ============================================================================


@router.get(
    "/{user_uuid}/count",
    response_model=FollowCountResponse,
    status_code=status.HTTP_200_OK,
    summary="Get follower and following counts",
    responses={
        200: {"description": "Follower and following counts"},
    },
)
async def get_follow_counts(
    user_uuid: UUID,
    db: Session = Depends(get_db),
) -> FollowCountResponse:
    """
    Get the follower and following counts for a user.

    Public endpoint. No authentication required.
    """
    follow_service = FollowService(db)

    return FollowCountResponse(
        user_uuid=user_uuid,
        followers_count=follow_service.count_followers(user_uuid),
        following_count=follow_service.count_following(user_uuid),
    )
