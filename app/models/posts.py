import enum
from sqlalchemy import Column, String, Enum, ForeignKey, Text
from app.models.base import BaseModel
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class PostStatus(enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"


class Post(BaseModel):

    __tablename__ = "posts"

    author_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid"), index=True, nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(Enum(PostStatus), nullable=False)

    # Relationships
    author = relationship("Users", back_populates="posts")

    def __repr__(self) -> str:
        """Return string representation of the model."""
        return f"<{self.__class__.__name__}(title={self.title},status={self.status.value}>"
