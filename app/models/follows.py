from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID as UUID_TYPE

from sqlalchemy import DateTime, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base
from app.utils.dates import utc_now

if TYPE_CHECKING:
    from app.models.users import User


class Follow(Base):
    """
    Self-referential many-to-many relationship for user follows.

    Uses a composite primary key (follower_uuid, followee_uuid) to ensure
    a user cannot follow the same user twice.

    Supports soft delete via deleted_at field. When a user unfollows,
    deleted_at is set instead of removing the row.

    Note: This is an association table and does NOT inherit from BaseModel
    as it doesn't need uuid or updated_at fields.
    """

    __tablename__ = "follows"

    # User who is following (the follower)
    follower_uuid: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.uuid"),
        nullable=False
    )
    # User who is being followed (the followee)
    followee_uuid: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.uuid"),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None
    )

    # Composite primary key ensures uniqueness of follower-followee pairs
    __table_args__ = (
        PrimaryKeyConstraint('follower_uuid', 'followee_uuid'),
    )

    # Relationships
    # Note: foreign_keys parameter is required because this table has TWO foreign keys
    # pointing to the same User table. SQLAlchemy needs explicit instruction on which
    # foreign key column to use for each relationship to avoid ambiguity.

    # The user who is doing the following (uses follower_uuid to join with User.uuid)
    follower: Mapped["User"] = relationship(
        "User",
        foreign_keys=[follower_uuid],
        back_populates="following"
    )
    # The user who is being followed (uses followee_uuid to join with User.uuid)
    followee: Mapped["User"] = relationship(
        "User",
        foreign_keys=[followee_uuid],
        back_populates="followers"
    )

    def __repr__(self) -> str:
        """Return string representation of the model."""
        return f"<{self.__class__.__name__}(follower_uuid={self.follower_uuid},followee_uuid={self.followee_uuid})>"
