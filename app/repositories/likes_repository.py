"""
Likes Repository Module

This repository handles data access for the Likes model (post likes).

IMPORTANT: Likes does NOT inherit from BaseModel, so this repository
does NOT inherit from BaseRepository. It works directly with the SQLAlchemy
session because:
    - Likes has a composite primary key (user_uuid, post_uuid)
    - Likes has no uuid field (BaseRepository assumes uuid PK)
    - Likes has no updated_at field

Soft delete: Likes supports soft delete via deleted_at. When a user
unlikes, deleted_at is set. When they re-like, deleted_at is cleared.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict, List, Optional, Union, overload
from uuid import UUID

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.likes import Likes
from app.schemas.base import PaginationParams
from app.utils.dates import utc_now
from app.utils.pagination import paginate

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from app.schemas.base import PaginatedResponse


class LikesRepository:
    """
    Repository for Likes model operations.

    Unlike other repositories, this does NOT inherit from BaseRepository
    because Likes uses a composite primary key instead of a UUID.

    All read queries automatically exclude soft-deleted records
    (deleted_at IS NULL) unless explicitly requested.
    """

    def __init__(self, db: Session):
        """
        Initialize LikesRepository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    # ========================================================================
    # LIKE / UNLIKE
    # ========================================================================

    def like(self, user_uuid: UUID, post_uuid: UUID) -> Likes:
        """
        Create a like relationship between a user and a post.

        If a soft-deleted like exists, it restores it instead of
        creating a duplicate.

        Args:
            user_uuid: UUID of the user who likes the post
            post_uuid: UUID of the post being liked

        Returns:
            The created or restored Likes instance
        """
        try:
            # Check if a soft-deleted like exists
            existing = self.db.query(Likes).filter(
                and_(
                    Likes.user_uuid == user_uuid,
                    Likes.post_uuid == post_uuid,
                )
            ).first()

            if existing:
                # Restore soft-deleted like
                existing.deleted_at = None
                existing.created_at = utc_now()
                self.db.flush()
                self.db.refresh(existing)
                return existing

            # Create new like
            like = Likes(
                user_uuid=user_uuid,
                post_uuid=post_uuid,
            )
            self.db.add(like)
            self.db.flush()
            self.db.refresh(like)
            return like
        except Exception as e:
            self.db.rollback()
            logger.error("Error creating like (user=%s, post=%s): %s", user_uuid, post_uuid, e)
            raise

    def unlike(self, user_uuid: UUID, post_uuid: UUID) -> bool:
        """
        Soft delete a like relationship.

        Args:
            user_uuid: UUID of the user
            post_uuid: UUID of the post

        Returns:
            True if the like was soft-deleted, False if it didn't exist
        """
        try:
            like = self.db.query(Likes).filter(
                and_(
                    Likes.user_uuid == user_uuid,
                    Likes.post_uuid == post_uuid,
                    Likes.deleted_at.is_(None),
                )
            ).first()

            if not like:
                return False

            like.deleted_at = utc_now()
            self.db.flush()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error("Error unliking (user=%s, post=%s): %s", user_uuid, post_uuid, e)
            raise

    # ========================================================================
    # READ OPERATIONS
    # ========================================================================

    def has_liked(self, user_uuid: UUID, post_uuid: UUID) -> bool:
        """
        Check if a user has an active like on a post.

        Args:
            user_uuid: UUID of the user
            post_uuid: UUID of the post

        Returns:
            True if an active like exists
        """
        return self.db.query(Likes).filter(
            and_(
                Likes.user_uuid == user_uuid,
                Likes.post_uuid == post_uuid,
                Likes.deleted_at.is_(None),
            )
        ).first() is not None

    @overload
    def get_post_likes(self, post_uuid: UUID, pagination: PaginationParams) -> PaginatedResponse[Likes]: ...

    @overload
    def get_post_likes(self, post_uuid: UUID, pagination: None = ...) -> List[Likes]: ...

    def get_post_likes(
        self,
        post_uuid: UUID,
        pagination: Optional[PaginationParams] = None,
    ) -> Union[List[Likes], PaginatedResponse[Likes]]:
        """
        Get all active likes for a post.

        Args:
            post_uuid: UUID of the post
            pagination: Optional pagination parameters

        Returns:
            List of Likes instances or PaginatedResponse if paginated
        """
        query = self.db.query(Likes).filter(
            and_(
                Likes.post_uuid == post_uuid,
                Likes.deleted_at.is_(None),
            )
        ).order_by(Likes.created_at.desc())

        if pagination:
            total_count = query.count()
            items = query.offset(pagination.skip).limit(pagination.limit).all()
            return paginate(items, pagination, total_count)

        return query.all()

    @overload
    def get_user_likes(self, user_uuid: UUID, pagination: PaginationParams) -> PaginatedResponse[Likes]: ...

    @overload
    def get_user_likes(self, user_uuid: UUID, pagination: None = ...) -> List[Likes]: ...

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
        """
        query = self.db.query(Likes).filter(
            and_(
                Likes.user_uuid == user_uuid,
                Likes.deleted_at.is_(None),
            )
        ).order_by(Likes.created_at.desc())

        if pagination:
            total_count = query.count()
            items = query.offset(pagination.skip).limit(pagination.limit).all()
            return paginate(items, pagination, total_count)

        return query.all()

    # ========================================================================
    # COUNT OPERATIONS
    # ========================================================================

    def count_post_likes(self, post_uuid: UUID) -> int:
        """
        Count active likes on a post.

        Args:
            post_uuid: UUID of the post

        Returns:
            Number of active likes
        """
        return self.db.query(func.count()).select_from(Likes).filter(
            and_(
                Likes.post_uuid == post_uuid,
                Likes.deleted_at.is_(None),
            )
        ).scalar() or 0

    def count_post_likes_batch(self, post_uuids: List[UUID]) -> Dict[UUID, int]:
        """
        Count active likes for multiple posts in a single query.

        Args:
            post_uuids: List of post UUIDs

        Returns:
            Dictionary mapping post_uuid to like count
        """
        if not post_uuids:
            return {}

        rows = self.db.query(
            Likes.post_uuid,
            func.count().label("cnt"),
        ).filter(
            and_(
                Likes.post_uuid.in_(post_uuids),
                Likes.deleted_at.is_(None),
            )
        ).group_by(Likes.post_uuid).all()

        counts = {row[0]: row[1] for row in rows}
        return {uuid: counts.get(uuid, 0) for uuid in post_uuids}

    def count_user_likes(self, user_uuid: UUID) -> int:
        """
        Count total likes given by a user.

        Args:
            user_uuid: UUID of the user

        Returns:
            Number of active likes by the user
        """
        return self.db.query(func.count()).select_from(Likes).filter(
            and_(
                Likes.user_uuid == user_uuid,
                Likes.deleted_at.is_(None),
            )
        ).scalar() or 0
