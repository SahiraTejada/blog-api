from sqlalchemy import Column,ForeignKey, Text
from app.models.base import BaseModel
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID




class Comments(BaseModel):

    __tablename__ = "comments"

    post_uuid = Column(UUID(as_uuid=True), ForeignKey("posts.uuid"), index=True, nullable=False)
    author_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid"), index=True, nullable=False)

    content = Column(Text, nullable=False)
    parent_comment_uuid = Column(UUID(as_uuid=True), ForeignKey("comments.uuid"), index=True, nullable=True)
    
    # Relationships
    author = relationship("Users", back_populates="comments")
    posts = relationship("Post", back_populates="comments")

    def __repr__(self) -> str:
        """Return string representation of the model."""
        return f"<{self.__class__.__name__}(post_uuid={self.post_uuid},content={self.status.content}>"
