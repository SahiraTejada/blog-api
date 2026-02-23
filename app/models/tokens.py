import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from uuid import UUID as UUID_TYPE

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.users import User


class TokenType(str, enum.Enum):
    """
    Token types for different authentication purposes.

    - ACCESS: Short-lived token for API access
    - REFRESH: Long-lived token to renew access tokens
    - RESET_PASSWORD: Token for password reset emails
    - EMAIL_VERIFICATION: Token for email verification
    """

    ACCESS = "access"
    REFRESH = "refresh"
    RESET_PASSWORD = "reset_password"
    EMAIL_VERIFICATION = "email_verification"


class Token(BaseModel):
    """
    Token model for JWT storage and management.

    Inherits uuid, created_at, updated_at, deleted_at from BaseModel.
    """

    __tablename__ = "tokens"

    # Token data
    user_uuid: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.uuid", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    token: Mapped[str] = mapped_column(
        String(500),
        unique=True,
        nullable=False,
        index=True
    )
    type: Mapped[TokenType] = mapped_column(
        Enum(TokenType),
        nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None
    )

    # Optional metadata for security
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        default=None
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="tokens"
    )

    def __repr__(self) -> str:
        """Return string representation of the model."""
        return f"<Token {self.uuid} - {self.type} - User: {self.user_uuid}>"

    @property
    def is_expired(self) -> bool:
        """Check if the token has expired."""
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_revoked(self) -> bool:
        """Check if the token has been revoked."""
        return self.revoked_at is not None

    @property
    def is_valid(self) -> bool:
        """Check if the token is valid (not expired, not revoked, not deleted)."""
        return not self.is_expired and not self.is_revoked and not self.deleted_at

    def revoke(self) -> None:
        """Revoke the token by setting the timestamp."""
        self.revoked_at = datetime.now(timezone.utc)
