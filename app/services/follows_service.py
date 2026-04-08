"""
Follow Service Module

This module provides follow management business logic including
follow/unfollow operations, follower/following lists, and statistics.

Architecture Flow:
    Route → FollowService → FollowRepository → Database

The FollowService handles:
    - Follow a user (with self-follow and duplicate prevention)
    - Unfollow a user
    - Check if a user is following another
    - Get followers and following lists
    - Follower/following counts
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Union, overload
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions.follow import (
    AlreadyFollowingException,
    CannotFollowSelfException,
    FollowNotFoundException,
)
from app.core.exceptions.user import UserNotFoundException
from app.models.follows import Follow
from app.repositories.follows_repository import FollowRepository
from app.repositories.user_repository import UserRepository
from app.schemas.base import PaginationParams

if TYPE_CHECKING:
    from app.schemas.base import PaginatedResponse


class FollowService:
    """
    Service for follow management operations.

    Does NOT inherit from BaseService because Follow uses a composite
    primary key and does not inherit from BaseModel.

    Attributes:
        follow_repo: FollowRepository instance for follow operations
        user_repo: UserRepository instance for user validation
    """

    def __init__(self, db: Session):
        """
        Initialize FollowService with database session.

        Args:
            db: SQLAlchemy database session from FastAPI dependency
        """
        self.follow_repo = FollowRepository(db)
        self.user_repo = UserRepository(db)

    # ========================================================================
    # FOLLOW / UNFOLLOW
    # ========================================================================

    def follow(self, follower_uuid: UUID, followee_uuid: UUID) -> Follow:
        """
        Follow a user.

        Validates that:
        - The user is not trying to follow themselves
        - Both users exist
        - The follow relationship doesn't already exist

        If a soft-deleted follow exists, the repository restores it.

        Args:
            follower_uuid: UUID of the user who wants to follow
            followee_uuid: UUID of the user to be followed

        Returns:
            The created or restored Follow instance

        Raises:
            CannotFollowSelfException: If follower and followee are the same
            UserNotFoundException: If either user does not exist
            AlreadyFollowingException: If already following (active)
        """
        if follower_uuid == followee_uuid:
            raise CannotFollowSelfException()

        # Validate both users exist
        follower = self.user_repo.get_by_uuid(follower_uuid)
        if not follower:
            raise UserNotFoundException(identifier=str(follower_uuid))

        followee = self.user_repo.get_by_uuid(followee_uuid)
        if not followee:
            raise UserNotFoundException(identifier=str(followee_uuid))

        # Check if already following (active)
        if self.follow_repo.is_following(follower_uuid, followee_uuid):
            raise AlreadyFollowingException()

        return self.follow_repo.follow(follower_uuid, followee_uuid)

    def unfollow(self, follower_uuid: UUID, followee_uuid: UUID) -> None:
        """
        Unfollow a user.

        Args:
            follower_uuid: UUID of the user who wants to unfollow
            followee_uuid: UUID of the user to be unfollowed

        Raises:
            FollowNotFoundException: If the follow relationship does not exist
        """
        unfollowed = self.follow_repo.unfollow(follower_uuid, followee_uuid)
        if not unfollowed:
            raise FollowNotFoundException()

    # ========================================================================
    # QUERIES
    # ========================================================================

    def is_following(self, follower_uuid: UUID, followee_uuid: UUID) -> bool:
        """
        Check if a user is following another user.

        Args:
            follower_uuid: UUID of the potential follower
            followee_uuid: UUID of the potential followee

        Returns:
            True if an active follow relationship exists
        """
        return self.follow_repo.is_following(follower_uuid, followee_uuid)

    @overload
    def get_followers(self, user_uuid: UUID, pagination: PaginationParams) -> PaginatedResponse[Follow]: ...

    @overload
    def get_followers(self, user_uuid: UUID, pagination: None = ...) -> List[Follow]: ...

    def get_followers(
        self,
        user_uuid: UUID,
        pagination: Optional[PaginationParams] = None,
    ) -> Union[List[Follow], PaginatedResponse[Follow]]:
        """
        Get all followers of a user.

        Args:
            user_uuid: UUID of the user whose followers to retrieve
            pagination: Optional pagination parameters

        Returns:
            List of Follow instances or PaginatedResponse if paginated

        Raises:
            UserNotFoundException: If the user does not exist
        """
        user = self.user_repo.get_by_uuid(user_uuid)
        if not user:
            raise UserNotFoundException(identifier=str(user_uuid))

        return self.follow_repo.get_followers(
            user_uuid=user_uuid,
            pagination=pagination,
        )

    @overload
    def get_following(self, user_uuid: UUID, pagination: PaginationParams) -> PaginatedResponse[Follow]: ...

    @overload
    def get_following(self, user_uuid: UUID, pagination: None = ...) -> List[Follow]: ...

    def get_following(
        self,
        user_uuid: UUID,
        pagination: Optional[PaginationParams] = None,
    ) -> Union[List[Follow], PaginatedResponse[Follow]]:
        """
        Get all users that a user is following.

        Args:
            user_uuid: UUID of the user whose following list to retrieve
            pagination: Optional pagination parameters

        Returns:
            List of Follow instances or PaginatedResponse if paginated

        Raises:
            UserNotFoundException: If the user does not exist
        """
        user = self.user_repo.get_by_uuid(user_uuid)
        if not user:
            raise UserNotFoundException(identifier=str(user_uuid))

        return self.follow_repo.get_following(
            user_uuid=user_uuid,
            pagination=pagination,
        )

    # ========================================================================
    # STATISTICS
    # ========================================================================

    def count_followers(self, user_uuid: UUID) -> int:
        """
        Count how many followers a user has.

        Args:
            user_uuid: UUID of the user

        Returns:
            Number of active followers
        """
        return self.follow_repo.count_followers(user_uuid)

    def count_following(self, user_uuid: UUID) -> int:
        """
        Count how many users a user is following.

        Args:
            user_uuid: UUID of the user

        Returns:
            Number of users being followed
        """
        return self.follow_repo.count_following(user_uuid)
