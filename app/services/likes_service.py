"""
Likes Service Module

This module provides like management business logic including
like/unlike, toggle, status checks, and statistics.

Architecture Flow:
    Route → LikesService → LikesRepository → Database

The LikesService handles:
    - Like a post (with duplicate prevention)
    - Unlike a post
    - Toggle like on a post
    - Check like status
    - Get likes for a post or by a user
    - Like count statistics
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Tuple, Union
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions.like import AlreadyLikedException, LikeNotFoundException
from app.core.exceptions.post import PostNotFoundException
from app.core.exceptions.user import UserNotFoundException
from app.models.likes import Likes
from app.repositories.likes_repository import LikesRepository
from app.repositories.post_repository import PostRepository
from app.repositories.user_repository import UserRepository
from app.schemas.base import PaginationParams

if TYPE_CHECKING:
    from app.schemas.base import PaginatedResponse


class LikesService:
    """
    Service for like management operations.

    Does NOT inherit from BaseService because Likes uses a composite
    primary key and does not inherit from BaseModel.

    Attributes:
        likes_repo: LikesRepository instance for like operations
        post_repo: PostRepository instance for post validation
        user_repo: UserRepository instance for user validation
    """

    def __init__(self, db: Session):
        """
        Initialize LikesService with database session.

        Args:
            db: SQLAlchemy database session from FastAPI dependency
        """
        self.likes_repo = LikesRepository(db)
        self.post_repo = PostRepository(db)
        self.user_repo = UserRepository(db)

    # ========================================================================
    # LIKE / UNLIKE
    # ========================================================================

    def like_post(self, user_uuid: UUID, post_uuid: UUID) -> Likes:
        """
        Like a post.

        Validates that the post exists and the user hasn't already liked it.

        Args:
            user_uuid: UUID of the user liking the post
            post_uuid: UUID of the post to like

        Returns:
            The created or restored Likes instance

        Raises:
            PostNotFoundException: If the post does not exist
            AlreadyLikedException: If the user already liked this post
        """
        post = self.post_repo.get_by_uuid(post_uuid)
        if not post:
            raise PostNotFoundException(identifier=str(post_uuid))

        if self.likes_repo.has_liked(user_uuid, post_uuid):
            raise AlreadyLikedException()

        return self.likes_repo.like(user_uuid, post_uuid)

    def unlike_post(self, user_uuid: UUID, post_uuid: UUID) -> None:
        """
        Unlike a post.

        Args:
            user_uuid: UUID of the user
            post_uuid: UUID of the post to unlike

        Raises:
            LikeNotFoundException: If the like does not exist
        """
        unliked = self.likes_repo.unlike(user_uuid, post_uuid)
        if not unliked:
            raise LikeNotFoundException()

    def toggle_like(self, user_uuid: UUID, post_uuid: UUID) -> Tuple[Optional[Likes], bool]:
        """
        Toggle like on a post.

        If the user has liked the post, unlike it.
        If not, like it.

        Args:
            user_uuid: UUID of the user
            post_uuid: UUID of the post

        Returns:
            Tuple of (Likes instance or None, liked: bool).
            - If liked: (Likes, True)
            - If unliked: (None, False)

        Raises:
            PostNotFoundException: If the post does not exist
        """
        post = self.post_repo.get_by_uuid(post_uuid)
        if not post:
            raise PostNotFoundException(identifier=str(post_uuid))

        if self.likes_repo.has_liked(user_uuid, post_uuid):
            self.likes_repo.unlike(user_uuid, post_uuid)
            return None, False

        like = self.likes_repo.like(user_uuid, post_uuid)
        return like, True

    # ========================================================================
    # QUERIES
    # ========================================================================

    def has_liked(self, user_uuid: UUID, post_uuid: UUID) -> bool:
        """
        Check if a user has liked a post.

        Args:
            user_uuid: UUID of the user
            post_uuid: UUID of the post

        Returns:
            True if the user has an active like on the post
        """
        return self.likes_repo.has_liked(user_uuid, post_uuid)

    def get_post_likes(
        self,
        post_uuid: UUID,
        pagination: Optional[PaginationParams] = None,
    ) -> Union[List[Likes], PaginatedResponse[Likes]]:
        """
        Get all likes for a post.

        Args:
            post_uuid: UUID of the post
            pagination: Optional pagination parameters

        Returns:
            List of Likes instances or PaginatedResponse if paginated

        Raises:
            PostNotFoundException: If the post does not exist
        """
        post = self.post_repo.get_by_uuid(post_uuid)
        if not post:
            raise PostNotFoundException(identifier=str(post_uuid))

        return self.likes_repo.get_post_likes(
            post_uuid=post_uuid,
            pagination=pagination,
        )

    def get_user_likes(
        self,
        user_uuid: UUID,
        pagination: Optional[PaginationParams] = None,
    ) -> Union[List[Likes], PaginatedResponse[Likes]]:
        """
        Get all posts liked by a user.

        Args:
            user_uuid: UUID of the user
            pagination: Optional pagination parameters

        Returns:
            List of Likes instances or PaginatedResponse if paginated

        Raises:
            UserNotFoundException: If the user does not exist
        """
        user = self.user_repo.get_by_uuid(user_uuid)
        if not user:
            raise UserNotFoundException(identifier=str(user_uuid))

        return self.likes_repo.get_user_likes(
            user_uuid=user_uuid,
            pagination=pagination,
        )

    # ========================================================================
    # STATISTICS
    # ========================================================================

    def count_post_likes(self, post_uuid: UUID) -> int:
        """
        Count likes on a post.

        Args:
            post_uuid: UUID of the post

        Returns:
            Number of active likes
        """
        return self.likes_repo.count_post_likes(post_uuid)

    def count_user_likes(self, user_uuid: UUID) -> int:
        """
        Count total likes given by a user.

        Args:
            user_uuid: UUID of the user

        Returns:
            Number of active likes by the user
        """
        return self.likes_repo.count_user_likes(user_uuid)
