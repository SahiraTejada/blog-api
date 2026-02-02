from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Column, ForeignKey, String, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

from app.models.posts import Post

post_categories = Table(
    'post_categories',
    BaseModel.metadata,
    Column('post_uuid', UUID(as_uuid=True), ForeignKey('posts.uuid'), primary_key=True),
    Column('category_uuid', UUID(as_uuid=True), ForeignKey('categories.uuid'), primary_key=True)
)


class Category(BaseModel):
    """Category model for organizing posts."""

    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        default=None
    )

    # Relationships
    posts: Mapped[List["Post"]] = relationship(
        "Post",
        secondary=post_categories,
        back_populates="categories"
    )

    def __repr__(self) -> str:
        """Return string representation of the model."""
        return f"<{self.__class__.__name__}(name={self.name})>"
