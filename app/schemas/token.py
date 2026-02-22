"""
Token Schemas Module

This module defines Pydantic schemas for token-related API operations.
These schemas handle validation, serialization, and documentation for
JWT token management endpoints.

Schema Types:
    - Create/Update: Internal schemas for database operations
    - Response: Public schemas for API responses (hide sensitive data)
    - OAuth2: Standard OAuth2-compliant response formats

Security Note:
    Response schemas are carefully designed to avoid exposing sensitive
    information. For example, TokenSessionSchema hides the actual JWT
    string when listing user sessions.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.models.tokens import TokenType
from app.schemas.base import BaseSchema, CreateSchema, ResponseSchema, UpdateSchema

# ============================================================================
# INTERNAL SCHEMAS (for service/repository use)
# ============================================================================


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
    Schema for FULL token data in API responses (ADMIN USE ONLY).

    WARNING: This schema exposes the actual JWT token string.
    Only use this for administrative endpoints that require full
    token visibility. For user-facing session lists, use TokenSessionSchema
    which hides the actual token.

    This schema inherits UUID and timestamps from ResponseSchema.
    It includes all token information for administrative/debugging purposes.

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


# ============================================================================
# OAUTH2-COMPLIANT RESPONSE SCHEMAS (for API responses)
# ============================================================================


class TokenPairResponseSchema(BaseSchema):
    """
    Schema for login response with both access and refresh tokens.

    This follows OAuth2 token response format and is used for:
    - Login endpoint responses
    - Token refresh endpoint responses (when rotating refresh token)

    Attributes:
        access_token: JWT access token for API authentication
        refresh_token: JWT refresh token for obtaining new access tokens
        token_type: Always "bearer" for JWT tokens
        expires_in: Seconds until access token expires

    Example:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "expires_in": 1800
        }
    """

    access_token: str = Field(
        description="JWT access token for API authentication",
        json_schema_extra={"example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
    )
    refresh_token: str = Field(
        description="JWT refresh token for obtaining new access tokens",
        json_schema_extra={"example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer' for JWT)"
    )
    expires_in: int = Field(
        description="Seconds until access token expires",
        json_schema_extra={"example": 1800}
    )


class AccessTokenResponseSchema(BaseSchema):
    """
    Schema for access token only response.

    Used when only returning an access token (e.g., refresh without rotation).

    Attributes:
        access_token: JWT access token
        token_type: Always "bearer"
        expires_in: Seconds until expiration

    Example:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "expires_in": 1800
        }
    """

    access_token: str = Field(
        description="JWT access token for API authentication",
        json_schema_extra={"example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer' for JWT)"
    )
    expires_in: int = Field(
        description="Seconds until access token expires",
        json_schema_extra={"example": 1800}
    )


class RefreshTokenResponseSchema(BaseSchema):
    """
    Schema for refresh token response.

    Returns a new access token (and optionally a new refresh token).
    Used by /auth/refresh endpoint.

    Attributes:
        access_token: New JWT access token
        refresh_token: New refresh token (optional, for token rotation)
        token_type: Type of token (always "bearer")
        expires_in: Time in seconds until access token expires

    Example:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "expires_in": 1800
        }
    """

    access_token: str = Field(
        description="New JWT access token",
        json_schema_extra={"example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
    )
    refresh_token: Optional[str] = Field(
        default=None,
        description="New refresh token (for token rotation)",
        json_schema_extra={"example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (always bearer for JWT)"
    )
    expires_in: int = Field(
        description="Time in seconds until access token expires",
        json_schema_extra={"example": 1800}
    )


# ============================================================================
# SESSION/ADMIN SCHEMAS (for user session management)
# ============================================================================


class TokenSessionSchema(BaseSchema):
    """
    Schema for displaying user sessions WITHOUT exposing the JWT.

    This is used for the "active sessions" endpoint where users can
    see their logged-in devices. The actual token is NOT included
    for security reasons.

    Attributes:
        uuid: Token identifier (for revocation)
        type: Token type (access, refresh)
        created_at: When the session was created
        expires_at: When the session expires
        ip_address: IP address of the session
        is_current: Whether this is the current session

    Example:
        {
            "uuid": "123e4567-e89b-12d3-a456-426614174000",
            "type": "access",
            "created_at": "2025-01-15T10:00:00Z",
            "expires_at": "2025-01-15T10:30:00Z",
            "ip_address": "192.168.1.1",
            "is_current": true
        }
    """

    uuid: UUID = Field(
        description="Token identifier (use this for revocation)"
    )
    type: TokenType = Field(
        description="Token type"
    )
    created_at: datetime = Field(
        description="When the session was created"
    )
    expires_at: datetime = Field(
        description="When the session expires"
    )
    ip_address: Optional[str] = Field(
        default=None,
        description="IP address of the session"
    )
    is_current: bool = Field(
        default=False,
        description="Whether this is the current session"
    )


class ActiveSessionsResponseSchema(BaseSchema):
    """
    Schema for listing all active sessions.

    Used by the "active sessions" or "manage devices" endpoint.

    Attributes:
        sessions: List of active sessions
        total: Total number of active sessions

    Example:
        {
            "sessions": [
                {
                    "uuid": "...",
                    "type": "access",
                    "created_at": "2025-01-15T10:00:00Z",
                    "ip_address": "192.168.1.1",
                    "is_current": true
                }
            ],
            "total": 3
        }
    """

    sessions: List[TokenSessionSchema] = Field(
        description="List of active sessions"
    )
    total: int = Field(
        description="Total number of active sessions"
    )


class RevokeTokensResponseSchema(BaseSchema):
    """
    Schema for token revocation response.

    Used by logout and "revoke sessions" endpoints.

    Attributes:
        message: Success message
        revoked_count: Number of tokens revoked

    Example:
        {
            "message": "Successfully logged out from 3 devices",
            "revoked_count": 3
        }
    """

    message: str = Field(
        description="Success message"
    )
    revoked_count: int = Field(
        description="Number of tokens/sessions revoked"
    )
