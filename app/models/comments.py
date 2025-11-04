from typing import TYPE_CHECKING, List, Optional
from uuid import UUID as UUID_TYPE

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.posts import Post
    from app.models.users import User


class Comments(BaseModel):
    """
    Comments model for post comments.

    Supports nested comments up to 2 levels (self-referential).
    """

    __tablename__ = "comments"

    post_uuid: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("posts.uuid"),
        index=True,
        nullable=False
    )
    author_uuid: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.uuid"),
        index=True,
        nullable=False
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    parent_comment_uuid: Mapped[Optional[UUID_TYPE]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("comments.uuid"),
        index=True,
        nullable=True,
        default=None
    )

    # Relationships
    author: Mapped["User"] = relationship(
        "User",
        back_populates="comments"
    )
    post: Mapped["Post"] = relationship(
        "Post",
        back_populates="comments"
    )

    # Self-referential relationship for nested comments
    replies: Mapped[List["Comments"]] = relationship(
        "Comments",
        backref="parent",
        remote_side="Comments.uuid",
        foreign_keys=[parent_comment_uuid]
    )

    def __repr__(self) -> str:
        """Return string representation of the model."""
        return f"<{self.__class__.__name__}(post_uuid={self.post_uuid},content={self.content[:50]})>"
