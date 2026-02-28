"""
Follow Repository Module

This repository handles data access for the Follow model (user follows).

IMPORTANT: Follow does NOT inherit from BaseModel, so this repository
does NOT inherit from BaseRepository. It works directly with the SQLAlchemy
session because:
    - Follow has a composite primary key (follower_uuid, followee_uuid)
    - Follow has no uuid field (BaseRepository assumes uuid PK)
    - Follow has no updated_at field

Soft delete: Follow supports soft delete via deleted_at. When a user
unfollows, deleted_at is set. When they re-follow, deleted_at is cleared.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional, Union
from uuid import UUID

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.follows import Follow
from app.schemas.base import PaginationParams
from app.utils.pagination import paginate

if TYPE_CHECKING:
    from app.schemas.base import PaginatedResponse


class FollowRepository:
    """
    Repository for Follow model operations.

    Unlike other repositories, this does NOT inherit from BaseRepository
    because Follow uses a composite primary key instead of a UUID.

    All read queries automatically exclude soft-deleted records
    (deleted_at IS NULL) unless explicitly requested.
    """

    def __init__(self, db: Session):
        """
        Initialize FollowRepository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    # ========================================================================
    # CREATE / DELETE (Follow / Unfollow)
    # ========================================================================

    def follow(self, follower_uuid: UUID, followee_uuid: UUID) -> Follow:
        """
        Create a follow relationship between two users.

        If a soft-deleted follow exists, it restores it instead of
        creating a duplicate.

        Args:
            follower_uuid: UUID of the user who wants to follow
            followee_uuid: UUID of the user being followed

        Returns:
            The created or restored Follow instance

        Raises:
            IntegrityError: If either user UUID doesn't exist
        """
        # Check if a soft-deleted follow exists
        existing = self.db.query(Follow).filter(
            and_(
                Follow.follower_uuid == follower_uuid,
                Follow.followee_uuid == followee_uuid,
            )
        ).first()

        if existing:
            # Restore soft-deleted follow
            existing.deleted_at = None
            existing.created_at = datetime.now(timezone.utc)
            self.db.flush()
            self.db.refresh(existing)
            return existing

        # Create new follow
        follow = Follow(
            follower_uuid=follower_uuid,
            followee_uuid=followee_uuid,
        )
        self.db.add(follow)
        self.db.flush()
        self.db.refresh(follow)
        return follow

    def unfollow(self, follower_uuid: UUID, followee_uuid: UUID) -> bool:
        """
        Soft delete a follow relationship between two users.

        Sets deleted_at instead of removing the row.

        Args:
            follower_uuid: UUID of the follower
            followee_uuid: UUID of the followee

        Returns:
            True if the relationship was soft-deleted, False if it didn't exist
        """
        follow = self.db.query(Follow).filter(
            and_(
                Follow.follower_uuid == follower_uuid,
                Follow.followee_uuid == followee_uuid,
                Follow.deleted_at.is_(None),
            )
        ).first()

        if not follow:
            return False

        follow.deleted_at = datetime.now(timezone.utc)
        self.db.flush()
        return True

    # ========================================================================
    # READ OPERATIONS
    # ========================================================================

    def is_following(self, follower_uuid: UUID, followee_uuid: UUID) -> bool:
        """
        Check if a user is following another user.

        Only considers active (non-deleted) follows.

        Args:
            follower_uuid: UUID of the potential follower
            followee_uuid: UUID of the potential followee

        Returns:
            True if an active follow relationship exists
        """
        return self.db.query(Follow).filter(
            and_(
                Follow.follower_uuid == follower_uuid,
                Follow.followee_uuid == followee_uuid,
                Follow.deleted_at.is_(None),
            )
        ).first() is not None

    def get_followers(
        self,
        user_uuid: UUID,
        pagination: Optional[PaginationParams] = None,
    ) -> Union[List[Follow], PaginatedResponse[Follow]]:
        """
        Get all active followers of a user (users who follow this user).

        Args:
            user_uuid: UUID of the user whose followers to retrieve
            pagination: Optional pagination parameters

        Returns:
            List of Follow instances or PaginatedResponse if paginated
        """
        query = self.db.query(Follow).filter(
            and_(
                Follow.followee_uuid == user_uuid,
                Follow.deleted_at.is_(None),
            )
        ).order_by(Follow.created_at.desc())

        if pagination:
            total_count = query.count()
            items = query.offset(pagination.skip).limit(pagination.limit).all()
            return paginate(items, pagination, total_count)

        return query.all()

    def get_following(
        self,
        user_uuid: UUID,
        pagination: Optional[PaginationParams] = None,
    ) -> Union[List[Follow], PaginatedResponse[Follow]]:
        """
        Get all users that a user is actively following.

        Args:
            user_uuid: UUID of the user whose following list to retrieve
            pagination: Optional pagination parameters

        Returns:
            List of Follow instances or PaginatedResponse if paginated
        """
        query = self.db.query(Follow).filter(
            and_(
                Follow.follower_uuid == user_uuid,
                Follow.deleted_at.is_(None),
            )
        ).order_by(Follow.created_at.desc())

        if pagination:
            total_count = query.count()
            items = query.offset(pagination.skip).limit(pagination.limit).all()
            return paginate(items, pagination, total_count)

        return query.all()

    # ========================================================================
    # COUNT OPERATIONS
    # ========================================================================

    def count_followers(self, user_uuid: UUID) -> int:
        """
        Count how many active followers a user has.

        Args:
            user_uuid: UUID of the user

        Returns:
            Number of active followers
        """
        return self.db.query(func.count()).select_from(Follow).filter(
            and_(
                Follow.followee_uuid == user_uuid,
                Follow.deleted_at.is_(None),
            )
        ).scalar() or 0

    def count_following(self, user_uuid: UUID) -> int:
        """
        Count how many users a user is actively following.

        Args:
            user_uuid: UUID of the user

        Returns:
            Number of users being followed
        """
        return self.db.query(func.count()).select_from(Follow).filter(
            and_(
                Follow.follower_uuid == user_uuid,
                Follow.deleted_at.is_(None),
            )
        ).scalar() or 0
