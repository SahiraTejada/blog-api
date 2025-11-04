from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Like(Base):

    __tablename__ = "likes"
    uuid = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)

    post_uuid = Column(UUID(as_uuid=True), ForeignKey("posts.uuid"), index=True, nullable=False)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid"), index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint('user_uuid', 'post_uuid', name='unique_user_post_like'),
    )

    # Relationships
    user = relationship("Users", back_populates="likes")
    posts = relationship("Post", back_populates="likes")

    def __repr__(self) -> str:
        """Return string representation of the model."""
        return f"<{self.__class__.__name__}(post_uuid={self.post_uuid},user_uuid={self.user_uuid}>"
