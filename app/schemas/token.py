from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.models.tokens import TokenType
from app.schemas.base import CreateSchema, ResponseSchema, UpdateSchema


class TokenCreateSchema(CreateSchema):
    """
    Schema for creating a new token.

    This schema is used when creating new tokens (access, refresh, password reset, etc.).
    The revoked fields are not included as they default to False/None.

    Attributes:
        user_uuid: UUID of the user this token belongs to
        token: JWT token string
        type: Type of token (access, refresh, reset_password, email_verification)
        expires_at: When the token expires
        ip_address: IP address associated with the token (optional)

    Example:
        {
            "user_uuid": "123e4567-e89b-12d3-a456-426614174000",
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "type": "access",
            "expires_at": "2025-01-15T12:00:00Z",
            "ip_address": "192.168.1.1"
        }
    """

    user_uuid: UUID = Field(
        description="UUID of the user this token belongs to"
    )
    token: str = Field(
        max_length=500,
        description="JWT token string",
        json_schema_extra={"example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
    )
    type: TokenType = Field(
        description="Type of token (access, refresh, reset_password, email_verification)"
    )
    expires_at: datetime = Field(
        description="Timestamp when the token expires"
    )
    ip_address: Optional[str] = Field(
        default=None,
        max_length=45,
        description="IP address associated with the token"
    )


class TokenUpdateSchema(UpdateSchema):
    """
    Schema for updating token information.

    All fields are optional to support partial updates (PATCH).
    This is primarily used for revoking tokens or updating metadata.

    Attributes:
        expires_at: New expiration timestamp
        revoked: Whether the token is revoked
        revoked_at: When the token was revoked
        ip_address: IP address associated with the token

    Example:
        {
            "revoked": true,
            "revoked_at": "2025-01-15T11:00:00Z"
        }
    """

    expires_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the token expires"
    )
    revoked: Optional[bool] = Field(
        default=None,
        description="Whether the token has been revoked"
    )
    revoked_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the token was revoked"
    )
    ip_address: Optional[str] = Field(
        default=None,
        max_length=45,
        description="IP address associated with the token"
    )


class TokenResponseSchema(ResponseSchema):
    """
    Schema for token data in API responses.

    This schema inherits UUID and timestamps from ResponseSchema.
    It includes all token information for administrative purposes.

    Attributes:
        uuid: Unique identifier (inherited)
        user_uuid: UUID of the user this token belongs to
        token: JWT token string
        type: Type of token
        expires_at: When the token expires
        revoked: Whether the token is revoked
        revoked_at: When the token was revoked (if applicable)
        ip_address: IP address associated with the token
        created_at: When token was created (inherited)
        updated_at: When token was last updated (inherited)
        deleted_at: Soft delete timestamp (inherited)

    Example:
        {
            "uuid": "123e4567-e89b-12d3-a456-426614174000",
            "user_uuid": "123e4567-e89b-12d3-a456-426614174001",
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "type": "access",
            "expires_at": "2025-01-15T12:00:00Z",
            "revoked": false,
            "revoked_at": null,
            "ip_address": "192.168.1.1",
            "created_at": "2025-01-15T10:00:00Z",
            "updated_at": "2025-01-15T10:00:00Z",
            "deleted_at": null
        }
    """

    user_uuid: UUID = Field(
        description="UUID of the user this token belongs to"
    )
    token: str = Field(
        description="JWT token string"
    )
    type: TokenType = Field(
        description="Type of token"
    )
    expires_at: datetime = Field(
        description="Timestamp when the token expires"
    )
    revoked: bool = Field(
        description="Whether the token has been revoked"
    )
    revoked_at: Optional[datetime] = Field(
        description="Timestamp when the token was revoked (null if not revoked)"
    )
    ip_address: Optional[str] = Field(
        description="IP address associated with the token"
    )
