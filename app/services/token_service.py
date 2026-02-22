"""
Token Service Module

This module provides the business logic layer for JWT token management.
It wraps TokenRepository with HTTP-level error handling and adds JWT
generation, validation, and lifecycle management.

Architecture Flow:
    Route → TokenService → TokenRepository → Database

The TokenService handles:
    - JWT token generation (access, refresh, password reset, email verification)
    - Token validation and verification
    - Token revocation (single token, all user tokens, all except current)
    - Session management (counting active sessions, enforcing limits)
    - Token cleanup (expired and revoked tokens)

Security Considerations:
    - Tokens are stored in database for revocation capability
    - Access tokens are short-lived (default: 30 minutes)
    - Refresh tokens are long-lived (default: 7 days)
    - IP address tracking for security auditing
    - Suspicious token detection based on IP changes
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

import jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import (
    InvalidTokenTypeException,
    TokenExpiredException,
    TokenInvalidException,
    TokenNotFoundException,
)
from app.models.tokens import Token, TokenType
from app.repositories.token_repository import TokenRepository
from app.services.base_service import BaseService


class TokenService(BaseService[Token]):
    """
    Service for managing JWT tokens with business logic validation.

    This service extends BaseService to provide token-specific operations
    including JWT generation, validation, revocation, and cleanup.

    Inherits from BaseService[Token]:
        - get_by_uuid(uuid) → Token or raises 404
        - list(pagination, filters, ...) → PaginatedResponse
        - create(data) → Token or raises 409
        - update(uuid, data) → Token or raises 404/409
        - delete(uuid) → None or raises 404

    Attributes:
        token_repo: TokenRepository instance for database operations
        repo: Alias for token_repo (inherited from BaseService)

    Example:
        # In a route or dependency
        def get_token_service(db: Session = Depends(get_db)):
            return TokenService(db)

        # Create access token for user
        token_data = token_service.create_access_token(
            user_uuid=user.uuid,
            ip_address=request.client.host
        )
    """

    def __init__(self, db: Session):
        """
        Initialize TokenService with database session.

        Creates a TokenRepository instance and passes it to BaseService.

        Args:
            db: SQLAlchemy database session from FastAPI dependency

        Example:
            token_service = TokenService(db)
        """
        # Create the token repository for database operations
        self.token_repo = TokenRepository(db)

        # Pass repository to BaseService for inherited CRUD methods
        super().__init__(self.token_repo)

    # ========================================================================
    # JWT GENERATION METHODS
    # ========================================================================

    def _generate_jwt(
        self,
        user_uuid: UUID,
        token_type: TokenType,
        expires_delta: timedelta
    ) -> tuple[str, datetime]:
        """
        Generate a JWT token string with the given parameters.

        This is a private helper method used by public token creation methods.
        The JWT payload includes:
            - sub: User UUID (subject)
            - type: Token type (access, refresh, etc.)
            - exp: Expiration timestamp
            - iat: Issued at timestamp

        Args:
            user_uuid: The UUID of the user this token belongs to
            token_type: Type of token (ACCESS, REFRESH, etc.)
            expires_delta: How long until the token expires

        Returns:
            Tuple of (jwt_string, expiration_datetime)

        Note:
            This method only generates the JWT string. It does NOT store
            the token in the database. Use create_access_token() or
            create_refresh_token() to create and store tokens.
        """
        # Calculate expiration time in UTC
        expires_at = datetime.now(timezone.utc) + expires_delta

        # Build the JWT payload with standard claims
        payload: Dict[str, Any] = {
            "sub": str(user_uuid),          # Subject: user identifier
            "type": token_type.value,        # Token type for validation
            "exp": expires_at,               # Expiration time
            "iat": datetime.now(timezone.utc)  # Issued at time
        }

        # Encode the JWT using the secret key and algorithm from settings
        token_string = jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )

        return token_string, expires_at

    def create_access_token(
        self,
        user_uuid: UUID,
        ip_address: Optional[str] = None
    ) -> Token:
        """
        Create a new access token for a user.

        Access tokens are short-lived (default: 30 minutes) and used
        for authenticating API requests. They are stored in the database
        to support revocation.

        Args:
            user_uuid: UUID of the user to create token for
            ip_address: Client IP address for security tracking (optional)

        Returns:
            Token: The created token model instance

        Raises:
            HTTPException 409: If token creation fails due to constraint

        Example:
            # In login endpoint
            access_token = token_service.create_access_token(
                user_uuid=user.uuid,
                ip_address=request.client.host
            )
            return {"access_token": access_token.token, "token_type": "bearer"}
        """
        # Calculate expiration from settings (default: 30 minutes)
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        # Generate the JWT string and get expiration datetime
        token_string, expires_at = self._generate_jwt(
            user_uuid=user_uuid,
            token_type=TokenType.ACCESS,
            expires_delta=expires_delta
        )

        # Prepare data for database storage
        token_data = {
            "user_uuid": user_uuid,
            "token": token_string,
            "type": TokenType.ACCESS,
            "expires_at": expires_at,
            "ip_address": ip_address
        }

        # Use inherited create() method which handles IntegrityError → 409
        return self.create(token_data)

    def create_refresh_token(
        self,
        user_uuid: UUID,
        ip_address: Optional[str] = None
    ) -> Token:
        """
        Create a new refresh token for a user.

        Refresh tokens are long-lived (default: 7 days) and used to
        obtain new access tokens without re-authentication. They should
        be stored securely by the client (e.g., httpOnly cookie).

        Args:
            user_uuid: UUID of the user to create token for
            ip_address: Client IP address for security tracking (optional)

        Returns:
            Token: The created token model instance

        Raises:
            HTTPException 409: If token creation fails due to constraint

        Example:
            # In login endpoint
            refresh_token = token_service.create_refresh_token(
                user_uuid=user.uuid,
                ip_address=request.client.host
            )
            # Set refresh token in httpOnly cookie
            response.set_cookie(
                key="refresh_token",
                value=refresh_token.token,
                httponly=True,
                secure=True
            )
        """
        # Calculate expiration from settings (default: 7 days)
        expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        # Generate the JWT string and get expiration datetime
        token_string, expires_at = self._generate_jwt(
            user_uuid=user_uuid,
            token_type=TokenType.REFRESH,
            expires_delta=expires_delta
        )

        # Prepare data for database storage
        token_data = {
            "user_uuid": user_uuid,
            "token": token_string,
            "type": TokenType.REFRESH,
            "expires_at": expires_at,
            "ip_address": ip_address
        }

        # Use inherited create() method which handles IntegrityError → 409
        return self.create(token_data)

    def create_token_pair(
        self,
        user_uuid: UUID,
        ip_address: Optional[str] = None
    ) -> Dict[str, Token]:
        """
        Create both access and refresh tokens for a user.

        This is a convenience method for login endpoints that need
        to issue both tokens at once.

        Args:
            user_uuid: UUID of the user to create tokens for
            ip_address: Client IP address for security tracking (optional)

        Returns:
            Dict with 'access' and 'refresh' Token instances

        Example:
            # In login endpoint
            tokens = token_service.create_token_pair(
                user_uuid=user.uuid,
                ip_address=request.client.host
            )
            return {
                "access_token": tokens["access"].token,
                "refresh_token": tokens["refresh"].token,
                "token_type": "bearer"
            }
        """
        access_token = self.create_access_token(user_uuid, ip_address)
        refresh_token = self.create_refresh_token(user_uuid, ip_address)

        return {
            "access": access_token,
            "refresh": refresh_token
        }

    # ========================================================================
    # TOKEN VALIDATION METHODS
    # ========================================================================

    def validate_token(
        self,
        token_string: str,
        expected_type: Optional[TokenType] = None
    ) -> Token:
        """
        Validate a token and return the Token model if valid.

        This method performs both JWT validation (signature, expiry)
        and database validation (exists, not revoked, not deleted).

        Args:
            token_string: The JWT token string to validate
            expected_type: If provided, verify token is of this type

        Returns:
            Token: The validated token model instance

        Raises:
            TokenExpiredException: If token has expired
            TokenInvalidException: If token is malformed or signature invalid
            InvalidTokenTypeException: If token type doesn't match expected
            TokenNotFoundException: If token not found or revoked

        Example:
            # In authentication middleware
            try:
                token = token_service.validate_token(
                    token_string=bearer_token,
                    expected_type=TokenType.ACCESS
                )
                # Token is valid, get user_uuid from token
                user_uuid = token.user_uuid
            except AppException:
                # Token is invalid
                raise
        """
        # Step 1: Decode and verify JWT signature and expiration
        try:
            payload = jwt.decode(
                token_string,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
        except jwt.ExpiredSignatureError:
            # Token has expired according to JWT exp claim
            raise TokenExpiredException()
        except jwt.InvalidTokenError:
            # Token is malformed or signature is invalid
            raise TokenInvalidException()

        # Step 2: Verify token type matches expected type (if specified)
        if expected_type:
            token_type_from_jwt = payload.get("type")
            if token_type_from_jwt != expected_type.value:
                raise InvalidTokenTypeException(
                    expected=expected_type.value,
                    received=token_type_from_jwt
                )

        # Step 3: Check token exists in database and is valid
        # This catches revoked tokens and ensures token was issued by us
        token = self.token_repo.get_valid_token(token_string, expected_type)

        if not token:
            raise TokenNotFoundException()

        return token

    def validate_access_token(self, token_string: str) -> Token:
        """
        Validate an access token.

        Convenience method that calls validate_token with ACCESS type.

        Args:
            token_string: The JWT access token string

        Returns:
            Token: The validated token model instance

        Raises:
            TokenExpiredException: If token has expired
            TokenInvalidException: If token is invalid
            InvalidTokenTypeException: If not an access token

        Example:
            # In protected route dependency
            token = token_service.validate_access_token(bearer_token)
            user = user_service.get_by_uuid(token.user_uuid)
        """
        return self.validate_token(token_string, TokenType.ACCESS)

    def validate_refresh_token(self, token_string: str) -> Token:
        """
        Validate a refresh token.

        Convenience method that calls validate_token with REFRESH type.

        Args:
            token_string: The JWT refresh token string

        Returns:
            Token: The validated token model instance

        Raises:
            TokenExpiredException: If token has expired
            TokenInvalidException: If token is invalid
            InvalidTokenTypeException: If not a refresh token

        Example:
            # In token refresh endpoint
            old_token = token_service.validate_refresh_token(refresh_token)
            new_tokens = token_service.refresh_tokens(old_token)
        """
        return self.validate_token(token_string, TokenType.REFRESH)

    def get_user_uuid_from_token(self, token_string: str) -> UUID:
        """
        Extract and validate user UUID from a token.

        Validates the token and returns the user UUID from it.
        This is useful when you only need the user ID, not the
        full token model.

        Args:
            token_string: The JWT token string

        Returns:
            UUID: The user's UUID from the token

        Raises:
            HTTPException 401: If token is invalid

        Example:
            # In route dependency
            user_uuid = token_service.get_user_uuid_from_token(bearer_token)
            user = user_service.get_by_uuid(user_uuid)
        """
        token = self.validate_token(token_string)
        return token.user_uuid

    # ========================================================================
    # TOKEN REFRESH METHODS
    # ========================================================================

    def refresh_tokens(
        self,
        refresh_token_string: str,
        ip_address: Optional[str] = None,
        rotate_refresh_token: bool = True
    ) -> Dict[str, Token]:
        """
        Use a refresh token to get new access (and optionally refresh) tokens.

        This implements the OAuth2 refresh token flow. The old refresh
        token is revoked to prevent reuse (token rotation).

        Args:
            refresh_token_string: The refresh token to use
            ip_address: Client IP address for the new tokens
            rotate_refresh_token: If True, also issue new refresh token

        Returns:
            Dict with 'access' and optionally 'refresh' Token instances

        Raises:
            HTTPException 401: If refresh token is invalid

        Example:
            # In /auth/refresh endpoint
            new_tokens = token_service.refresh_tokens(
                refresh_token_string=old_refresh_token,
                ip_address=request.client.host
            )
            return {
                "access_token": new_tokens["access"].token,
                "refresh_token": new_tokens.get("refresh", {}).token,
                "token_type": "bearer"
            }
        """
        # Validate the refresh token (raises 401 if invalid)
        old_token = self.validate_refresh_token(refresh_token_string)
        user_uuid = old_token.user_uuid

        # Revoke the old refresh token (token rotation for security)
        self.revoke_token(refresh_token_string)

        # Create new access token
        new_access = self.create_access_token(user_uuid, ip_address)

        result: Dict[str, Token] = {"access": new_access}

        # Optionally create new refresh token (token rotation)
        if rotate_refresh_token:
            new_refresh = self.create_refresh_token(user_uuid, ip_address)
            result["refresh"] = new_refresh

        return result

    # ========================================================================
    # TOKEN REVOCATION METHODS
    # ========================================================================

    def revoke_token(self, token_string: str) -> bool:
        """
        Revoke a single token (logout from one device).

        This marks the token as revoked in the database. The token
        will no longer pass validation even if not expired.

        Args:
            token_string: The token to revoke

        Returns:
            bool: True if token was revoked, False if not found

        Example:
            # In logout endpoint
            token_service.revoke_token(access_token)
            return {"message": "Logged out successfully"}
        """
        return self.token_repo.revoke_token(token_string)

    def revoke_all_user_tokens(
        self,
        user_uuid: UUID,
        token_type: Optional[TokenType] = None
    ) -> int:
        """
        Revoke all tokens for a user (logout from all devices).

        Use this for "logout everywhere" functionality or when
        a user changes their password.

        Args:
            user_uuid: UUID of the user
            token_type: Optional filter by token type

        Returns:
            int: Number of tokens revoked

        Example:
            # In "logout everywhere" endpoint
            count = token_service.revoke_all_user_tokens(current_user.uuid)
            return {"message": f"Logged out from {count} devices"}

            # When user changes password (revoke all access tokens)
            token_service.revoke_all_user_tokens(
                user.uuid,
                token_type=TokenType.ACCESS
            )
        """
        return self.token_repo.revoke_user_tokens(
            user_uuid=user_uuid,
            token_type=token_type
        )

    def revoke_all_except_current(
        self,
        user_uuid: UUID,
        current_token: str
    ) -> int:
        """
        Revoke all user tokens except the current one.

        Use this for "logout other sessions" functionality where
        the user wants to stay logged in on current device but
        logout everywhere else.

        Args:
            user_uuid: UUID of the user
            current_token: Token to keep active (current session)

        Returns:
            int: Number of tokens revoked

        Example:
            # In "logout other devices" endpoint
            count = token_service.revoke_all_except_current(
                user_uuid=current_user.uuid,
                current_token=bearer_token
            )
            return {"message": f"Logged out from {count} other devices"}
        """
        return self.token_repo.revoke_all_except(
            user_uuid=user_uuid,
            keep_token=current_token
        )

    # ========================================================================
    # SESSION MANAGEMENT METHODS
    # ========================================================================

    def get_user_tokens(
        self,
        user_uuid: UUID,
        token_type: Optional[TokenType] = None,
        include_revoked: bool = False,
        include_expired: bool = False
    ) -> List[Token]:
        """
        Get all tokens for a user.

        Useful for displaying active sessions to the user.

        Args:
            user_uuid: UUID of the user
            token_type: Optional filter by token type
            include_revoked: Include revoked tokens
            include_expired: Include expired tokens

        Returns:
            List[Token]: List of token instances

        Example:
            # In "active sessions" endpoint
            sessions = token_service.get_user_tokens(
                user_uuid=current_user.uuid,
                token_type=TokenType.ACCESS
            )
            return [
                {"ip": t.ip_address, "created": t.created_at}
                for t in sessions
            ]
        """
        return self.token_repo.get_user_tokens(
            user_uuid=user_uuid,
            token_type=token_type,
            include_revoked=include_revoked,
            include_expired=include_expired
        )

    def count_active_sessions(self, user_uuid: UUID) -> int:
        """
        Count active sessions (access tokens) for a user.

        Useful for enforcing maximum concurrent sessions.

        Args:
            user_uuid: UUID of the user

        Returns:
            int: Number of active sessions

        Example:
            # Enforce max 5 concurrent sessions
            if token_service.count_active_sessions(user.uuid) >= 5:
                raise HTTPException(
                    status_code=429,
                    detail="Maximum sessions reached. Please logout from another device."
                )
        """
        return self.token_repo.count_active_sessions(user_uuid)

    def enforce_session_limit(
        self,
        user_uuid: UUID,
        max_sessions: int = 5
    ) -> None:
        """
        Enforce maximum concurrent sessions by revoking oldest tokens.

        Call this before creating new tokens to ensure user doesn't
        exceed the session limit.

        Args:
            user_uuid: UUID of the user
            max_sessions: Maximum allowed concurrent sessions

        Example:
            # In login endpoint
            token_service.enforce_session_limit(user.uuid, max_sessions=5)
            tokens = token_service.create_token_pair(user.uuid)
        """
        active_tokens = self.token_repo.get_user_tokens(
            user_uuid=user_uuid,
            token_type=TokenType.ACCESS,
            include_revoked=False,
            include_expired=False
        )

        # If at or over limit, revoke oldest tokens
        if len(active_tokens) >= max_sessions:
            # Sort by created_at ascending (oldest first)
            sorted_tokens = sorted(active_tokens, key=lambda t: t.created_at)

            # Revoke oldest tokens to make room
            tokens_to_revoke = len(active_tokens) - max_sessions + 1
            for token in sorted_tokens[:tokens_to_revoke]:
                self.token_repo.revoke_token(token.token)

    # ========================================================================
    # SECURITY AND AUDITING METHODS
    # ========================================================================

    def get_suspicious_tokens(
        self,
        user_uuid: UUID,
        current_ip: str
    ) -> List[Token]:
        """
        Find tokens used from different IP addresses.

        Useful for detecting potentially stolen tokens.

        Args:
            user_uuid: UUID of the user
            current_ip: The current request's IP address

        Returns:
            List[Token]: Tokens from different IP addresses

        Example:
            # In security middleware
            suspicious = token_service.get_suspicious_tokens(
                user.uuid,
                request.client.host
            )
            if suspicious:
                # Alert user about suspicious activity
                send_security_alert(user.email)
        """
        return self.token_repo.get_suspicious_tokens(user_uuid, current_ip)

    def revoke_suspicious_tokens(
        self,
        user_uuid: UUID,
        current_ip: str
    ) -> int:
        """
        Revoke all tokens from different IP addresses.

        Call this if suspicious activity is detected.

        Args:
            user_uuid: UUID of the user
            current_ip: The current (trusted) IP address

        Returns:
            int: Number of tokens revoked

        Example:
            # User clicks "secure my account"
            count = token_service.revoke_suspicious_tokens(
                user.uuid,
                request.client.host
            )
            return {"message": f"Revoked {count} suspicious sessions"}
        """
        suspicious_tokens = self.get_suspicious_tokens(user_uuid, current_ip)
        count = 0

        for token in suspicious_tokens:
            if self.token_repo.revoke_token(token.token):
                count += 1

        return count

    # ========================================================================
    # CLEANUP METHODS
    # ========================================================================

    def cleanup_expired_tokens(
        self,
        older_than_days: int = 7,
        hard_delete: bool = True
    ) -> int:
        """
        Delete expired tokens from the database.

        This should be run periodically (e.g., daily cron job) to
        keep the database clean.

        Args:
            older_than_days: Only delete tokens expired for X days
            hard_delete: If True, permanently delete. If False, soft delete

        Returns:
            int: Number of tokens deleted

        Example:
            # In a scheduled task
            deleted = token_service.cleanup_expired_tokens()
            logger.info(f"Cleaned up {deleted} expired tokens")
        """
        return self.token_repo.cleanup_expired(
            hard_delete=hard_delete,
            older_than_days=older_than_days
        )

    def cleanup_revoked_tokens(
        self,
        older_than_days: int = 30,
        hard_delete: bool = True
    ) -> int:
        """
        Delete revoked tokens from the database.

        Revoked tokens are kept longer than expired ones for
        auditing purposes.

        Args:
            older_than_days: Only delete tokens revoked X days ago
            hard_delete: If True, permanently delete. If False, soft delete

        Returns:
            int: Number of tokens deleted

        Example:
            # In a monthly scheduled task
            deleted = token_service.cleanup_revoked_tokens(older_than_days=30)
            logger.info(f"Cleaned up {deleted} revoked tokens")
        """
        return self.token_repo.cleanup_revoked(
            hard_delete=hard_delete,
            older_than_days=older_than_days
        )

    def full_cleanup(self) -> Dict[str, int]:
        """
        Perform full token cleanup (expired and revoked).

        Convenience method to run all cleanup operations at once.

        Returns:
            Dict with 'expired' and 'revoked' counts

        Example:
            # In a daily scheduled task
            result = token_service.full_cleanup()
            logger.info(f"Cleanup: {result['expired']} expired, {result['revoked']} revoked")
        """
        return {
            "expired": self.cleanup_expired_tokens(),
            "revoked": self.cleanup_revoked_tokens()
        }
