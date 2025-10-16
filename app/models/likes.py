from sqlalchemy import Column,ForeignKey
from app.models.base import BaseModel
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID


class Likes(BaseModel):

    __tablename__ = "likes"

    post_uuid = Column(UUID(as_uuid=True), ForeignKey("posts.uuid"), index=True, nullable=False)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid"), index=True, nullable=False)

    # Relationships
    user = relationship("Users", back_populates="likes")
    posts = relationship("Post", back_populates="likes")

    def __repr__(self) -> str:
        """Return string representation of the model."""
        return f"<{self.__class__.__name__}(post_uuid={self.post_uuid},user_uuid={self.user_uuid}>"
