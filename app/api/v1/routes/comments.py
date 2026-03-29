"""
Comment Routes Module

This module provides API endpoints for comment management operations including:
- Create a comment on a post (authenticated users)
- List top-level comments for a post (public, paginated)
- Get full comment tree for a post (public, nested)
- Get a single comment by UUID (public)
- Get replies to a comment (public, paginated)
- Update a comment (author or admin)
- Delete a comment (author or admin)
- Get comment count for a post (public)

All endpoints follow REST conventions and return standardized responses.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import AuthContext, require_user
from app.database.session import get_db
from app.schemas.base import PaginatedResponse, PaginationParams, SuccessResponse
from app.schemas.comment import (
    CommentCountResponse,
    CommentCreateSchema,
    CommentListResponse,
    CommentResponse,
    CommentTreeNode,
    CommentUpdateSchema,
    CommentWithAuthorResponse,
)
from app.services.comment_service import CommentService

router = APIRouter(prefix="/comments", tags=["Comments"])


# ============================================================================
# COMMENT CREATION
# ============================================================================


@router.post(
    "/",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new comment",
    responses={
        201: {"description": "Comment created successfully"},
        400: {"description": "Parent comment does not belong to this post"},
        401: {"description": "Invalid or missing token"},
        404: {"description": "Post or parent comment not found"},
        422: {"description": "Validation error"},
    },
)
async def create_comment(
    data: CommentCreateSchema,
    auth: AuthContext = Depends(require_user),
    db: Session = Depends(get_db),
) -> CommentResponse:
    """
    Create a new comment on a post.

    Requires authentication. The author is set from the authenticated user's token.

    - **content**: Comment text (1-5000 characters)
    - **post_uuid**: UUID of the post to comment on
    - **parent_comment_uuid**: Optional UUID of parent comment (for replies)

    For top-level comments, omit parent_comment_uuid.
    For replies, the parent comment must belong to the same post.
    """
    comment_service = CommentService(db)

    comment = comment_service.create_comment(
        content=data.content,
        post_uuid=data.post_uuid,
        author_uuid=auth.user.uuid,
        parent_comment_uuid=data.parent_comment_uuid,
    )

    return CommentResponse.model_validate(comment)


# ============================================================================
# COMMENT LISTING & LOOKUP
# ============================================================================


@router.get(
    "/post/{post_uuid}",
    response_model=CommentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List top-level comments for a post",
    responses={
        200: {"description": "Paginated list of top-level comments"},
        404: {"description": "Post not found"},
    },
)
async def list_post_comments(
    post_uuid: UUID,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
) -> CommentListResponse:
    """
    List top-level comments for a post with pagination.

    Public endpoint. No authentication required.
    Returns only root-level comments (not replies).
    Use the comment tree endpoint or replies endpoint for nested comments.
    """
    comment_service = CommentService(db)

    result = comment_service.get_comments_by_post(
        post_uuid=post_uuid,
        pagination=pagination,
    )

    assert isinstance(result, PaginatedResponse)

    return CommentListResponse(
        data=[CommentWithAuthorResponse.model_validate(c) for c in result.data],
        pagination=result.pagination,
    )


@router.get(
    "/post/{post_uuid}/tree",
    response_model=List[CommentTreeNode],
    status_code=status.HTTP_200_OK,
    summary="Get full comment tree for a post",
    responses={
        200: {"description": "Nested comment tree"},
        404: {"description": "Post not found"},
    },
)
async def get_comment_tree(
    post_uuid: UUID,
    db: Session = Depends(get_db),
) -> List[CommentTreeNode]:
    """
    Get the full nested comment tree for a post.

    Public endpoint. No authentication required.
    Returns all comments assembled into a tree structure
    with unlimited nesting depth, fetched in a single query.
    """
    comment_service = CommentService(db)

    tree = comment_service.get_comment_tree(post_uuid)

    return [
        _build_tree_node(node)
        for node in tree
    ]


@router.get(
    "/post/{post_uuid}/count",
    response_model=CommentCountResponse,
    status_code=status.HTTP_200_OK,
    summary="Get comment count for a post",
    responses={
        200: {"description": "Total comment count"},
    },
)
async def get_post_comment_count(
    post_uuid: UUID,
    db: Session = Depends(get_db),
) -> CommentCountResponse:
    """
    Get the total number of comments on a post (all nesting levels).

    Public endpoint. No authentication required.
    """
    comment_service = CommentService(db)

    total = comment_service.count_by_post(post_uuid)

    return CommentCountResponse(
        post_uuid=post_uuid,
        total_comments=total,
    )


@router.get(
    "/{comment_uuid}",
    response_model=CommentWithAuthorResponse,
    status_code=status.HTTP_200_OK,
    summary="Get comment by UUID",
    responses={
        200: {"description": "Comment details"},
        404: {"description": "Comment not found"},
    },
)
async def get_comment(
    comment_uuid: UUID,
    db: Session = Depends(get_db),
) -> CommentWithAuthorResponse:
    """
    Get a single comment by UUID.

    Public endpoint. No authentication required.
    """
    comment_service = CommentService(db)

    comment = comment_service.get_by_comment_uuid(comment_uuid)

    return CommentWithAuthorResponse.model_validate(comment)


@router.get(
    "/{comment_uuid}/replies",
    response_model=CommentListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get replies to a comment",
    responses={
        200: {"description": "Paginated list of replies"},
        404: {"description": "Comment not found"},
    },
)
async def get_comment_replies(
    comment_uuid: UUID,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
) -> CommentListResponse:
    """
    Get direct replies to a specific comment with pagination.

    Public endpoint. No authentication required.
    Returns only the immediate children, not the full subtree.
    """
    comment_service = CommentService(db)

    result = comment_service.get_replies(
        comment_uuid=comment_uuid,
        pagination=pagination,
    )

    assert isinstance(result, PaginatedResponse)

    return CommentListResponse(
        data=[CommentWithAuthorResponse.model_validate(c) for c in result.data],
        pagination=result.pagination,
    )


# ============================================================================
# COMMENT UPDATE
# ============================================================================


@router.patch(
    "/{comment_uuid}",
    response_model=CommentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a comment",
    responses={
        200: {"description": "Comment updated successfully"},
        401: {"description": "Invalid or missing token"},
        404: {"description": "Comment not found"},
        422: {"description": "Validation error"},
    },
)
async def update_comment(
    comment_uuid: UUID,
    update_data: CommentUpdateSchema,
    auth: AuthContext = Depends(require_user),
    db: Session = Depends(get_db),
) -> CommentResponse:
    """
    Update a comment's content.

    Requires authentication.

    - **content**: New comment text (1-5000 characters)
    """
    comment_service = CommentService(db)

    updated_comment = comment_service.update_comment(
        comment_uuid=comment_uuid,
        update_data=update_data.model_dump(exclude_unset=True),
    )

    return CommentResponse.model_validate(updated_comment)


# ============================================================================
# COMMENT DELETION
# ============================================================================


@router.delete(
    "/{comment_uuid}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a comment",
    responses={
        200: {"description": "Comment deleted successfully"},
        401: {"description": "Invalid or missing token"},
        404: {"description": "Comment not found"},
    },
)
async def delete_comment(
    comment_uuid: UUID,
    auth: AuthContext = Depends(require_user),
    db: Session = Depends(get_db),
) -> SuccessResponse:
    """
    Soft-delete a comment.

    Requires authentication.
    The comment data is retained but marked as deleted.
    """
    comment_service = CommentService(db)

    comment_service.delete_comment(comment_uuid)

    return SuccessResponse(message="Comment deleted successfully")


# ============================================================================
# PRIVATE HELPERS
# ============================================================================


def _build_tree_node(node: dict) -> CommentTreeNode:
    """
    Recursively convert a repository tree dict into a CommentTreeNode schema.

    Args:
        node: Dict with 'comment' (Comments model) and 'replies' (list of dicts)

    Returns:
        CommentTreeNode with nested replies
    """
    return CommentTreeNode(
        comment=CommentWithAuthorResponse.model_validate(node["comment"]),
        replies=[_build_tree_node(child) for child in node["replies"]],
    )
