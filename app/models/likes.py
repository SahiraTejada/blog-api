from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID as UUID_TYPE

from sqlalchemy import DateTime, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base
from app.utils.dates import utc_now

if TYPE_CHECKING:
    from app.models.posts import Post
    from app.models.users import User


class Likes(Base):
    """
    Likes model for post likes.

    A user can like a post only once (enforced by composite primary key).

    Note: This is an association table and does NOT inherit from BaseModel
    as it doesn't need uuid or updated_at fields.
    """

    __tablename__ = "likes"

    user_uuid: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.uuid"),
        nullable=False
    )
    post_uuid: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("posts.uuid"),
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

    __table_args__ = (
        PrimaryKeyConstraint('user_uuid', 'post_uuid'),
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_uuid],
        back_populates="likes"
    )
    post: Mapped["Post"] = relationship(
        "Post",
        foreign_keys=[post_uuid],
        back_populates="likes"
    )

    def __repr__(self) -> str:
        """Return string representation of the model."""
        return f"<{self.__class__.__name__}(post_uuid={self.post_uuid},user_uuid={self.user_uuid})>"
