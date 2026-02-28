from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.posts import post_categories

if TYPE_CHECKING:
    from app.models.posts import Post


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
