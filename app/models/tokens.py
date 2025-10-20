import enum
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class TokenType(str, enum.Enum):
    ACCESS = "access"
    REFRESH = "refresh"
    RESET_PASSWORD = "reset_password"
    EMAIL_VERIFICATION = "email_verification"


class Token(Base):
    __tablename__ = "tokens"

    uuid = Column(UUID(as_uuid=True), unique=True, primary_key=True, index=True, default=uuid4)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid", ondelete="CASCADE"), nullable=False)
    token = Column(String, unique=True, nullable=False, index=True)
    type: Mapped[TokenType] = mapped_column(Enum(TokenType))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("Users", back_populates="tokens")

    def __repr__(self):
        return f"<Token {self.token_uuid} - {self.type} - User: {self.user_uuid}>"

    @property
    def is_expired(self):
        """Check if the token has expired"""
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_revoked(self):
        """Check if the token has been revoked"""
        return self.revoked is not None

    @property
    def is_valid(self):
        """Check if the token is valid (not expired and not revoked)"""
        return not self.is_expired and not self.is_revoked

    def revoke(self):
        """Revoke the token by setting the revoked timestamp"""
        self.revoked = datetime.now(timezone.utc)
