import enum

from sqlalchemy import Column, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.categories import post_categories


class PostStatus(enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"


class Post(BaseModel):

    __tablename__ = "posts"

    author_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid"), index=True, nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    status: Mapped[PostStatus] = mapped_column(Enum(PostStatus))

    # Relationships
    author = relationship("Users", back_populates="posts")
    comments = relationship("Comments", back_populates="posts")
    likes = relationship("Likes", back_populates="posts")

    categories = relationship(
            "Category",
            secondary=post_categories,
            back_populates="posts"
    )

    def __repr__(self) -> str:
        """Return string representation of the model."""
        return f"<{self.__class__.__name__}(title={self.title},status={self.status.value}>"
