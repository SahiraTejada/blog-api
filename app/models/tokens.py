from sqlalchemy import Column, String, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
import enum
from app.database.connection import Base


class TokenType(str, enum.Enum):
    ACCESS = "access"
    REFRESH = "refresh"
    RESET_PASSWORD = "reset_password"
    EMAIL_VERIFICATION = "email_verification"


class Token(Base):
    __tablename__ = "tokens"

    uuid = Column(UUID(as_uuid=True), unique=True,primary_key=True, index=True, default=uuid4)

    user_uuid = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_uuid", ondelete="CASCADE"),
        nullable=False
    )

    token = Column(String, unique=True, nullable=False, index=True)

    type = Column(Enum(TokenType), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(DateTime, nullable=True)  

    # Relationships
    user = relationship("User", back_populates="tokens")

    def __repr__(self):
        return f"<Token {self.token_uuid} - {self.type} - User: {self.user_uuid}>"

    @property
    def is_expired(self):
        """Verifica si el token ha expirado"""
        return datetime.utcnow() > self.expires_at

    @property
    def is_revoked(self):
        """Verifica si el token ha sido revocado"""
        return self.revoked is not None

    @property
    def is_valid(self):
        """Verifica si el token es válido (no expirado ni revocado)"""
        return not self.is_expired and not self.is_revoked

    def revoke(self):
        """Revoca el token"""
        self.revoked = datetime.utcnow()