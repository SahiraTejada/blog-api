from sqlalchemy import Column,ForeignKey,DateTime
from datetime import datetime, timezone
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4


class Likes():

    __tablename__ = "likes"
    uuid = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)

    post_uuid = Column(UUID(as_uuid=True), ForeignKey("posts.uuid"), index=True, nullable=False)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid"), index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("Users", back_populates="likes")
    posts = relationship("Post", back_populates="likes")

    def __repr__(self) -> str:
        """Return string representation of the model."""
        return f"<{self.__class__.__name__}(post_uuid={self.post_uuid},user_uuid={self.user_uuid}>"
