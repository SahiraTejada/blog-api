import enum
from typing import TYPE_CHECKING, List
from uuid import UUID as UUID_TYPE

from sqlalchemy import Column, Enum, ForeignKey, String, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.categories import Category
    from app.models.comments import Comments
    from app.models.likes import Likes
    from app.models.users import User


post_categories: Table = Table(
    "post_categories",
    BaseModel.metadata,
    Column("post_uuid", UUID(as_uuid=True), ForeignKey("posts.uuid"), primary_key=True),
    Column("category_uuid", UUID(as_uuid=True), ForeignKey("categories.uuid"), primary_key=True),
)


class PostStatus(enum.Enum):
    """
    Post publication status.

    - DRAFT: Post is not published yet
    - PUBLISHED: Post is publicly visible
    """

    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"


class Post(BaseModel):
    """Post model for blog articles."""

    __tablename__ = "posts"

    author_uuid: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.uuid"),
        index=True,
        nullable=False
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    status: Mapped[PostStatus] = mapped_column(
        Enum(PostStatus),
        default=PostStatus.DRAFT,
        nullable=False
    )

    # Relationships
    author: Mapped["User"] = relationship(
        "User",
        back_populates="posts"
    )
    comments: Mapped[List["Comments"]] = relationship(
        "Comments",
        back_populates="post"
    )
    likes: Mapped[List["Likes"]] = relationship(
        "Likes",
        back_populates="post"
    )
    categories: Mapped[List["Category"]] = relationship(
        "Category",
        secondary=post_categories,
        back_populates="posts"
    )

    def __repr__(self) -> str:
        """Return string representation of the model."""
        return f"<{self.__class__.__name__}(title={self.title},status={self.status.value})>"
