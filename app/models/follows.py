from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Follows(Base):
    """
    Self-referential many-to-many relationship for user follows.

    Uses a composite primary key (follower_uuid, followee_uuid) to ensure
    a user cannot follow the same user twice.
    """

    __tablename__ = "follows"

    # User who is following (the follower)
    follower_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid"), nullable=False)
    # User who is being followed (the followee)
    followee_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Composite primary key ensures uniqueness of follower-followee pairs
    __table_args__ = (
        PrimaryKeyConstraint('follower_uuid', 'followee_uuid'),
    )

    # Relationships
    # Note: foreign_keys parameter is required because this table has TWO foreign keys
    # pointing to the same Users table. SQLAlchemy needs explicit instruction on which
    # foreign key column to use for each relationship to avoid ambiguity.

    # The user who is doing the following (uses follower_uuid to join with Users.uuid)
    follower = relationship("Users", foreign_keys=[follower_uuid], back_populates="following")
    # The user who is being followed (uses followee_uuid to join with Users.uuid)
    followee = relationship("Users", foreign_keys=[followee_uuid], back_populates="followers")

    def __repr__(self) -> str:
        """Return string representation of the model."""
        return f"<{self.__class__.__name__}(follower_uuid={self.follower_uuid},followee_uuid={self.followee_uuid}>"
