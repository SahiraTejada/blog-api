"""
Comment Service Module

This module provides comment management business logic including
comment creation, retrieval, updates, deletion, and nested threading.

Architecture Flow:
    Route → CommentService → CommentRepository → Database

The CommentService handles:
    - Comment creation on a post (top-level or reply)
    - Parent comment validation (exists + belongs to same post)
    - Comment retrieval by UUID, post, or author
    - Comment tree building for nested threads
    - Comment updates (content only)
    - Comment deletion (soft delete)
    - Comment statistics (counts by post, author)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions.comment import (
    CommentNotFoundException,
    CommentPostMismatchException,
    ParentCommentNotFoundException,
)
from app.core.exceptions.post import PostNotFoundException
from app.models.comments import Comments
from app.repositories.comment_repository import CommentRepository
from app.repositories.post_repository import PostRepository
from app.schemas.base import PaginationParams
from app.services.base_service import BaseService

if TYPE_CHECKING:
    from app.schemas.base import PaginatedResponse


class CommentService(BaseService[Comments]):
    """
    Service for comment management operations.

    Handles comment CRUD with nested threading support.
    Comments belong to a post and can be replies to other comments
    with unlimited nesting depth.

    Attributes:
        comment_repo: CommentRepository instance for database operations
        post_repo: PostRepository instance for post validation
    """

    def __init__(self, db: Session):
        """
        Initialize CommentService with database session.

        Args:
            db: SQLAlchemy database session from FastAPI dependency
        """
        self.comment_repo = CommentRepository(db)
        self.post_repo = PostRepository(db)
        super().__init__(self.comment_repo)

    # ========================================================================
    # COMMENT CREATION
    # ========================================================================

    def create_comment(
        self,
        content: str,
        post_uuid: UUID,
        author_uuid: UUID,
        parent_comment_uuid: Optional[UUID] = None,
    ) -> Comments:
        """
        Create a new comment on a post.

        For top-level comments, omit parent_comment_uuid.
        For replies, provide parent_comment_uuid — it must exist
        and belong to the same post.

        Args:
            content: Comment text content
            post_uuid: UUID of the post being commented on
            author_uuid: UUID of the comment author
            parent_comment_uuid: UUID of the parent comment (for replies)

        Returns:
            The created comment model instance

        Raises:
            PostNotFoundException: If the post does not exist
            ParentCommentNotFoundException: If the parent comment does not exist
            CommentPostMismatchException: If the parent comment belongs to a different post
        """
        # Validate post exists
        post = self.post_repo.get_by_uuid(post_uuid)
        if not post:
            raise PostNotFoundException(identifier=str(post_uuid))

        # Validate parent comment if this is a reply
        if parent_comment_uuid:
            self._validate_parent_comment(parent_comment_uuid, post_uuid)

        comment_data: Dict[str, Any] = {
            "content": content,
            "post_uuid": post_uuid,
            "author_uuid": author_uuid,
            "parent_comment_uuid": parent_comment_uuid,
        }

        return self.create(comment_data)

    # ========================================================================
    # COMMENT RETRIEVAL
    # ========================================================================

    def get_by_comment_uuid(self, comment_uuid: UUID) -> Comments:
        """
        Get a comment by UUID.

        Args:
            comment_uuid: UUID of the comment to retrieve

        Returns:
            The comment model instance

        Raises:
            CommentNotFoundException: If comment does not exist
        """
        comment = self.comment_repo.get_by_uuid(comment_uuid)
        if not comment:
            raise CommentNotFoundException(identifier=str(comment_uuid))
        return comment

    def get_comments_by_post(
        self,
        post_uuid: UUID,
        pagination: Optional[PaginationParams] = None,
    ) -> Union[List[Comments], PaginatedResponse[Comments]]:
        """
        Get top-level comments for a post.

        Args:
            post_uuid: UUID of the post
            pagination: Optional pagination parameters

        Returns:
            List of top-level comments or PaginatedResponse if pagination provided

        Raises:
            PostNotFoundException: If the post does not exist
        """
        post = self.post_repo.get_by_uuid(post_uuid)
        if not post:
            raise PostNotFoundException(identifier=str(post_uuid))

        return self.comment_repo.get_by_post_uuid(
            post_uuid=post_uuid,
            pagination=pagination,
        )

    def get_comment_tree(self, post_uuid: UUID) -> List[Dict[str, Any]]:
        """
        Get the full nested comment tree for a post.

        Returns all comments assembled into a tree structure
        with unlimited nesting depth, fetched in a single query.

        Args:
            post_uuid: UUID of the post

        Returns:
            List of top-level comment tree nodes, each with nested replies

        Raises:
            PostNotFoundException: If the post does not exist
        """
        post = self.post_repo.get_by_uuid(post_uuid)
        if not post:
            raise PostNotFoundException(identifier=str(post_uuid))

        return self.comment_repo.get_comment_tree(post_uuid)

    def get_replies(
        self,
        comment_uuid: UUID,
        pagination: Optional[PaginationParams] = None,
    ) -> Union[List[Comments], PaginatedResponse[Comments]]:
        """
        Get direct replies to a specific comment.

        Args:
            comment_uuid: UUID of the parent comment
            pagination: Optional pagination parameters

        Returns:
            List of reply comments or PaginatedResponse if pagination provided

        Raises:
            CommentNotFoundException: If the parent comment does not exist
        """
        comment = self.comment_repo.get_by_uuid(comment_uuid)
        if not comment:
            raise CommentNotFoundException(identifier=str(comment_uuid))

        return self.comment_repo.get_replies(
            parent_comment_uuid=comment_uuid,
            pagination=pagination,
        )

    def get_comments_by_author(
        self,
        author_uuid: UUID,
        pagination: Optional[PaginationParams] = None,
    ) -> Union[List[Comments], PaginatedResponse[Comments]]:
        """
        Get all comments by a specific author.

        Args:
            author_uuid: UUID of the author
            pagination: Optional pagination parameters

        Returns:
            List of comments or PaginatedResponse if pagination provided
        """
        return self.comment_repo.get_by_author_uuid(
            author_uuid=author_uuid,
            pagination=pagination,
        )

    # ========================================================================
    # COMMENT STATISTICS
    # ========================================================================

    def count_by_post(self, post_uuid: UUID) -> int:
        """
        Count total comments for a post (all nesting levels).

        Args:
            post_uuid: UUID of the post

        Returns:
            Total number of comments on the post
        """
        return self.comment_repo.count_by_post(post_uuid)

    def count_by_author(self, author_uuid: UUID) -> int:
        """
        Count total comments by a user.

        Args:
            author_uuid: UUID of the author

        Returns:
            Total number of comments by the user
        """
        return self.comment_repo.count_by_author(author_uuid)

    def count_replies(self, comment_uuid: UUID) -> int:
        """
        Count direct replies to a comment.

        Args:
            comment_uuid: UUID of the parent comment

        Returns:
            Number of direct replies
        """
        return self.comment_repo.count_replies(comment_uuid)

    # ========================================================================
    # COMMENT UPDATE
    # ========================================================================

    def update_comment(
        self,
        comment_uuid: UUID,
        update_data: Dict[str, Any],
    ) -> Comments:
        """
        Update a comment's content.

        Args:
            comment_uuid: UUID of the comment to update
            update_data: Dictionary with fields to update (only 'content' allowed)

        Returns:
            The updated comment model instance

        Raises:
            CommentNotFoundException: If comment does not exist
        """
        comment = self.comment_repo.get_by_uuid(comment_uuid)
        if not comment:
            raise CommentNotFoundException(identifier=str(comment_uuid))

        updated_comment = self.comment_repo.update(comment_uuid, update_data)
        if not updated_comment:
            raise CommentNotFoundException(identifier=str(comment_uuid))

        return updated_comment

    # ========================================================================
    # COMMENT DELETION
    # ========================================================================

    def delete_comment(self, comment_uuid: UUID) -> None:
        """
        Soft-delete a comment.

        Args:
            comment_uuid: UUID of the comment to delete

        Raises:
            CommentNotFoundException: If comment does not exist
        """
        deleted = self.comment_repo.delete(comment_uuid)
        if not deleted:
            raise CommentNotFoundException(identifier=str(comment_uuid))

    # ========================================================================
    # PRIVATE HELPERS
    # ========================================================================

    def _validate_parent_comment(
        self,
        parent_comment_uuid: UUID,
        post_uuid: UUID,
    ) -> None:
        """
        Validate that a parent comment exists and belongs to the same post.

        Args:
            parent_comment_uuid: UUID of the parent comment
            post_uuid: UUID of the post

        Raises:
            ParentCommentNotFoundException: If parent comment does not exist
            CommentPostMismatchException: If parent belongs to a different post
        """
        if not self.comment_repo.parent_exists(parent_comment_uuid):
            raise ParentCommentNotFoundException(identifier=str(parent_comment_uuid))

        if not self.comment_repo.parent_belongs_to_post(parent_comment_uuid, post_uuid):
            raise CommentPostMismatchException()
