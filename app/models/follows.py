from sqlalchemy import Column,ForeignKey,DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from app.database.connection import Base


class Follows(Base):

    __tablename__ = "follows"

    follower_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid"), index=True, nullable=False)
    followee_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid"), index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    follower = relationship("Users", back_populates="follows")
    followee = relationship("Users", back_populates="follows")

    def __repr__(self) -> str:
        """Return string representation of the model."""
        return f"<{self.__class__.__name__}(follower_uuid={self.follower_uuid},followee_uuid={self.followee_uuid}>"
