from typing import TYPE_CHECKING
from uuid import UUID as UUID_TYPE

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.posts import Post
    from app.models.users import User


class Likes(BaseModel):
    """
    Likes model for post likes.

    A user can like a post only once (enforced by unique constraint).
    Inherits uuid, created_at, updated_at, deleted_at from BaseModel.
    """

    __tablename__ = "likes"

    post_uuid: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("posts.uuid"),
        index=True,
        nullable=False
    )
    user_uuid: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.uuid"),
        index=True,
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint('user_uuid', 'post_uuid', name='unique_user_post_like'),
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="likes"
    )
    post: Mapped["Post"] = relationship(
        "Post",
        back_populates="likes"
    )

    def __repr__(self) -> str:
        """Return string representation of the model."""
        return f"<{self.__class__.__name__}(post_uuid={self.post_uuid},user_uuid={self.user_uuid})>"
