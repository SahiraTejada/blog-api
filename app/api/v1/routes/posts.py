"""
Post Routes Module

This module provides API endpoints for post management operations including:
- Create a new post (authenticated users)
- List all posts (public, paginated, with filters)
- Get post by UUID (public)
- Update post (author or admin)
- Delete post (author or admin)

All endpoints follow REST conventions and return standardized responses.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import AuthContext, require_user
from app.database.session import get_db
from app.schemas.base import SuccessResponse
from app.schemas.post import (
    PostCreateSchema,
    PostListRequest,
    PostListResponse,
    PostResponse,
    PostUpdateSchema,
)
from app.services.post_service import PostService

router = APIRouter(prefix="/posts", tags=["Posts"])


# ============================================================================
# POST CREATION
# ============================================================================


@router.post(
    "/",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new post",
    responses={
        201: {"description": "Post created successfully"},
        401: {"description": "Invalid or missing token"},
        409: {"description": "Post title already exists"},
        422: {"description": "Validation error"},
    },
)
async def create_post(
    data: PostCreateSchema,
    auth: AuthContext = Depends(require_user),
    db: Session = Depends(get_db),
) -> PostResponse:
    """
    Create a new post.

    Requires authentication. The author is set from the authenticated user's token.

    - **title**: Unique post title (1-255 characters)
    - **content**: Post content
    - **status**: Publication status (DRAFT or PUBLISHED, default: DRAFT)
    - **category_uuids**: Optional list of category UUIDs to assign
    """
    post_service = PostService(db)

    post = post_service.create_post(
        title=data.title,
        content=data.content,
        author_uuid=auth.user.uuid,
        status=data.status,
        category_uuids=data.category_uuids,
    )

    return PostResponse.model_validate(post)


# ============================================================================
# POST LISTING & LOOKUP
# ============================================================================


@router.get(
    "/",
    response_model=PostListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all posts",
    responses={
        200: {"description": "Paginated list of posts"},
    },
)
async def list_posts(
    filters: PostListRequest = Depends(),
    db: Session = Depends(get_db),
) -> PostListResponse:
    """
    List all posts with optional search, filters, and pagination.

    Public endpoint. No authentication required.

    - **search_term**: Searches across post title and content
    - **author_uuid**: Filter by author UUID
    - **category_uuid**: Filter by category UUID
    - **status**: Filter by publication status (DRAFT or PUBLISHED)
    """
    post_service = PostService(db)

    result = post_service.get_all_posts(
        pagination=filters,
        status=filters.status,
        search_term=filters.search_term,
        category_uuid=filters.category_uuid,
        author_uuid=filters.author_uuid,
    )

    return PostListResponse(
        data=[PostResponse.model_validate(post) for post in result.data],
        pagination=result.pagination,
    )


@router.get(
    "/{post_uuid}",
    response_model=PostResponse,
    status_code=status.HTTP_200_OK,
    summary="Get post by UUID",
    responses={
        200: {"description": "Post details"},
        404: {"description": "Post not found"},
    },
)
async def get_post(
    post_uuid: UUID,
    db: Session = Depends(get_db),
) -> PostResponse:
    """
    Get a post by UUID.

    Public endpoint. No authentication required.
    """
    post_service = PostService(db)

    post = post_service.get_by_post_uuid(post_uuid)

    return PostResponse.model_validate(post)


# ============================================================================
# POST UPDATE
# ============================================================================


@router.patch(
    "/{post_uuid}",
    response_model=PostResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a post",
    responses={
        200: {"description": "Post updated successfully"},
        401: {"description": "Invalid or missing token"},
        403: {"description": "Not the post author or admin"},
        404: {"description": "Post not found"},
        409: {"description": "Post title already exists"},
        422: {"description": "Validation error"},
    },
)
async def update_post(
    post_uuid: UUID,
    update_data: PostUpdateSchema,
    auth: AuthContext = Depends(require_user),
    db: Session = Depends(get_db),
) -> PostResponse:
    """
    Update a post.

    Only the post author or an admin can update a post.
    Only provided fields will be updated (partial update).

    - **title**: New post title (must be unique)
    - **content**: New post content
    - **status**: New publication status
    - **category_uuids**: New list of category UUIDs (replaces existing)
    """
    post_service = PostService(db)

    updated_post = post_service.update_post(
        post_uuid=post_uuid,
        update_data=update_data.model_dump(exclude_unset=True),
        current_user=auth.user,
    )

    return PostResponse.model_validate(updated_post)


# ============================================================================
# POST DELETION
# ============================================================================


@router.delete(
    "/{post_uuid}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a post",
    responses={
        200: {"description": "Post deleted successfully"},
        401: {"description": "Invalid or missing token"},
        403: {"description": "Not the post author or admin"},
        404: {"description": "Post not found"},
    },
)
async def delete_post(
    post_uuid: UUID,
    auth: AuthContext = Depends(require_user),
    db: Session = Depends(get_db),
) -> SuccessResponse:
    """
    Soft-delete a post.

    Only the post author or an admin can delete a post.
    The post data is retained but marked as deleted.
    """
    post_service = PostService(db)

    post_service.delete_post(
        post_uuid=post_uuid,
        current_user=auth.user,
    )

    return SuccessResponse(message="Post deleted successfully")
