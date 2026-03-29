"""
Likes Routes Module

This module provides API endpoints for like management operations including:
- Like a post (authenticated)
- Unlike a post (authenticated)
- Toggle like on a post (authenticated)
- Check if a post is liked (authenticated)
- List users who liked a post (public, paginated)
- List posts liked by a user (public, paginated)
- Get like count for a post (public)

All endpoints follow REST conventions and return standardized responses.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import AuthContext, require_user
from app.database.session import get_db
from app.schemas.base import PaginatedResponse, SuccessResponse
from app.schemas.likes import (
    LikeCountResponse,
    LikeCreateSchema,
    LikeListRequest,
    LikeListResponse,
    LikeResponse,
    LikeStatusResponse,
    LikeToggleResponse,
    LikeWithUserResponse,
)
from app.services.likes_service import LikesService

router = APIRouter(prefix="/likes", tags=["Likes"])


# ============================================================================
# LIKE / UNLIKE
# ============================================================================


@router.post(
    "/",
    response_model=LikeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Like a post",
    responses={
        201: {"description": "Successfully liked the post"},
        401: {"description": "Invalid or missing token"},
        404: {"description": "Post not found"},
        409: {"description": "Already liked this post"},
    },
)
async def like_post(
    data: LikeCreateSchema,
    auth: AuthContext = Depends(require_user),
    db: Session = Depends(get_db),
) -> LikeResponse:
    """
    Like a post.

    Requires authentication. The user is inferred from the token.

    - **post_uuid**: UUID of the post to like
    """
    likes_service = LikesService(db)

    like = likes_service.like_post(
        user_uuid=auth.user.uuid,
        post_uuid=data.post_uuid,
    )

    return LikeResponse.model_validate(like)


@router.delete(
    "/{post_uuid}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Unlike a post",
    responses={
        200: {"description": "Successfully unliked the post"},
        401: {"description": "Invalid or missing token"},
        404: {"description": "Like not found"},
    },
)
async def unlike_post(
    post_uuid: UUID,
    auth: AuthContext = Depends(require_user),
    db: Session = Depends(get_db),
) -> SuccessResponse:
    """
    Unlike a post.

    Requires authentication. The user is inferred from the token.
    """
    likes_service = LikesService(db)

    likes_service.unlike_post(
        user_uuid=auth.user.uuid,
        post_uuid=post_uuid,
    )

    return SuccessResponse(message="Successfully unliked the post")


# ============================================================================
# TOGGLE
# ============================================================================


@router.post(
    "/toggle/{post_uuid}",
    response_model=LikeToggleResponse,
    status_code=status.HTTP_200_OK,
    summary="Toggle like on a post",
    responses={
        200: {"description": "Like toggled successfully"},
        401: {"description": "Invalid or missing token"},
        404: {"description": "Post not found"},
    },
)
async def toggle_like(
    post_uuid: UUID,
    auth: AuthContext = Depends(require_user),
    db: Session = Depends(get_db),
) -> LikeToggleResponse:
    """
    Toggle like on a post.

    If the user has liked the post, it will be unliked.
    If not, it will be liked. Returns the new state and updated count.

    Requires authentication.
    """
    likes_service = LikesService(db)

    _like, liked = likes_service.toggle_like(
        user_uuid=auth.user.uuid,
        post_uuid=post_uuid,
    )

    likes_count = likes_service.count_post_likes(post_uuid)

    return LikeToggleResponse(liked=liked, likes_count=likes_count)


# ============================================================================
# LIKE STATUS
# ============================================================================


@router.get(
    "/status/{post_uuid}",
    response_model=LikeStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Check if a post is liked",
    responses={
        200: {"description": "Like status"},
        401: {"description": "Invalid or missing token"},
    },
)
async def check_like_status(
    post_uuid: UUID,
    auth: AuthContext = Depends(require_user),
    db: Session = Depends(get_db),
) -> LikeStatusResponse:
    """
    Check if the authenticated user has liked a post.

    Requires authentication.
    """
    likes_service = LikesService(db)

    has_liked = likes_service.has_liked(
        user_uuid=auth.user.uuid,
        post_uuid=post_uuid,
    )

    return LikeStatusResponse(has_liked=has_liked)


# ============================================================================
# LIKE LISTS
# ============================================================================


@router.get(
    "/post/{post_uuid}",
    response_model=LikeListResponse,
    status_code=status.HTTP_200_OK,
    summary="List users who liked a post",
    responses={
        200: {"description": "Paginated list of likes"},
        404: {"description": "Post not found"},
    },
)
async def list_post_likes(
    post_uuid: UUID,
    pagination: LikeListRequest = Depends(),
    db: Session = Depends(get_db),
) -> LikeListResponse:
    """
    List all users who liked a post with pagination.

    Public endpoint. No authentication required.
    """
    likes_service = LikesService(db)

    result = likes_service.get_post_likes(
        post_uuid=post_uuid,
        pagination=pagination,
    )

    assert isinstance(result, PaginatedResponse)

    return LikeListResponse(
        data=[
            LikeWithUserResponse(
                user_uuid=like.user_uuid,
                post_uuid=like.post_uuid,
                created_at=like.created_at,
                user=like.user,
            )
            for like in result.data
        ],
        pagination=result.pagination,
    )


@router.get(
    "/user/{user_uuid}",
    response_model=LikeListResponse,
    status_code=status.HTTP_200_OK,
    summary="List posts liked by a user",
    responses={
        200: {"description": "Paginated list of likes"},
        404: {"description": "User not found"},
    },
)
async def list_user_likes(
    user_uuid: UUID,
    pagination: LikeListRequest = Depends(),
    db: Session = Depends(get_db),
) -> LikeListResponse:
    """
    List all posts liked by a user with pagination.

    Public endpoint. No authentication required.
    """
    likes_service = LikesService(db)

    result = likes_service.get_user_likes(
        user_uuid=user_uuid,
        pagination=pagination,
    )

    assert isinstance(result, PaginatedResponse)

    return LikeListResponse(
        data=[
            LikeWithUserResponse(
                user_uuid=like.user_uuid,
                post_uuid=like.post_uuid,
                created_at=like.created_at,
                user=like.user,
            )
            for like in result.data
        ],
        pagination=result.pagination,
    )


# ============================================================================
# STATISTICS
# ============================================================================


@router.get(
    "/post/{post_uuid}/count",
    response_model=LikeCountResponse,
    status_code=status.HTTP_200_OK,
    summary="Get like count for a post",
    responses={
        200: {"description": "Like count for the post"},
    },
)
async def get_like_count(
    post_uuid: UUID,
    db: Session = Depends(get_db),
) -> LikeCountResponse:
    """
    Get the like count for a post.

    Public endpoint. No authentication required.
    """
    likes_service = LikesService(db)

    return LikeCountResponse(
        post_uuid=post_uuid,
        likes_count=likes_service.count_post_likes(post_uuid),
    )
