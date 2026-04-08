from datetime import timedelta

from app.utils.dates import utc_now
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models import Token, TokenType
from app.repositories.base_repository import BaseRepository


class TokenRepository(BaseRepository[Token]):
    """
    Repository for Token model operations.

    Manages JWT tokens stored in database for revocation,
    session management, and security auditing.
    """

    def __init__(self, db: Session):
        """Initialize TokenRepository with Token model."""
        super().__init__(Token, db)

    # ====================================================================
    # TOKEN LOOKUP METHODS
    # ====================================================================

    def get_by_token(
        self,
        token: str,
        include_deleted: bool = False
    ) -> Optional[Token]:
        """
        Get a token by its string value.

        Args:
            token: The token string (JWT)
            include_deleted: If True, includes soft-deleted tokens

        Returns:
            Token instance if found, None otherwise

        Example:
            token_obj = token_repo.get_by_token("eyJhbGc...")
        """
        return self.get_by_text_field({"token": token}, case_insensitive=False, include_deleted=include_deleted)

    def get_valid_token(
        self,
        token: str,
        token_type: Optional[TokenType] = None
    ) -> Optional[Token]:
        """
        Get a token only if it's valid (not expired, not revoked).

        This is the main method for authentication middleware.

        Args:
            token: The token string
            token_type: Optional filter by token type

        Returns:
            Token instance if valid, None otherwise

        Example:
            # In authentication middleware
            token_obj = token_repo.get_valid_token(token_string)
            if not token_obj:
                raise HTTPException(401, "Invalid or expired token")
        """
        query = self.db.query(self.model).filter(
            and_(
                self.model.token == token,
                self.model.revoked_at.is_(None),
                self.model.deleted_at.is_(None),
                self.model.expires_at > utc_now()
            )
        )

        if token_type:
            query = query.filter(self.model.type == token_type)

        return query.first()

    # ====================================================================
    # USER TOKEN MANAGEMENT
    # ====================================================================

    def get_user_tokens(
        self,
        user_uuid: UUID,
        token_type: Optional[TokenType] = None,
        include_revoked: bool = False,
        include_expired: bool = False
    ) -> List[Token]:
        """
        Get all tokens for a specific user.

        Args:
            user_uuid: The user's UUID
            token_type: Optional filter by token type
            include_revoked: If True, includes revoked tokens
            include_expired: If True, includes expired tokens

        Returns:
            List of token instances

        Example:
            # Get all active access tokens for a user
            active_tokens = token_repo.get_user_tokens(
                user_uuid=user.uuid,
                token_type=TokenType.ACCESS
            )
        """
        filters: Dict[str, Any] = {"user_uuid": user_uuid}

        if token_type:
            filters["type"] = token_type

        tokens = self.filter_by(
            include_deleted=False,
            **filters
        )

        # Filter by revoked/expired status
        result = []
        for token in tokens:
            if not include_revoked and token.is_revoked:
                continue
            if not include_expired and token.is_expired:
                continue
            result.append(token)

        return result

    def count_active_sessions(
        self,
        user_uuid: UUID,
        token_type: TokenType = TokenType.ACCESS
    ) -> int:
        """
        Count active (valid) sessions for a user.

        Useful for enforcing maximum concurrent sessions.

        Args:
            user_uuid: The user's UUID
            token_type: Token type to count (default: ACCESS)

        Returns:
            Number of active sessions

        Example:
            # Enforce max 5 devices
            if token_repo.count_active_sessions(user.uuid) >= 5:
                raise HTTPException(429, "Too many active sessions")
        """
        tokens = self.get_user_tokens(
            user_uuid=user_uuid,
            token_type=token_type,
            include_revoked=False,
            include_expired=False
        )
        return len(tokens)

    # ====================================================================
    # TOKEN REVOCATION
    # ====================================================================

    def revoke_token(
        self,
        token: str,
        hard_delete: bool = False
    ) -> bool:
        """
        Revoke a specific token (logout from one device).

        Args:
            token: The token string to revoke
            hard_delete: If True, permanently delete. Default: mark as revoked

        Returns:
            True if revoked, False if not found

        Example:
            # In logout endpoint
            if token_repo.revoke_token(token_string):
                return {"message": "Logged out successfully"}
        """
        token_obj = self.get_by_token(token)

        if not token_obj:
            return False

        if hard_delete:
            return self.delete(token_obj.uuid, hard_delete=True)
        else:
            # Mark as revoked by setting revoked_at timestamp
            self.update(token_obj.uuid, {
                "revoked_at": utc_now()
            })
            return True

    def revoke_user_tokens(
        self,
        user_uuid: UUID,
        token_type: Optional[TokenType] = None,
        except_token: Optional[str] = None
    ) -> int:
        """
        Revoke all tokens for a user (logout from all devices).

        Args:
            user_uuid: The user's UUID
            token_type: Optional filter by token type
            except_token: Optional token to NOT revoke (current session)

        Returns:
            Number of tokens revoked

        Example:
            # Logout from all devices
            count = token_repo.revoke_user_tokens(user.uuid)
            return {"message": f"Logged out from {count} devices"}

            # Logout from all OTHER devices (keep current)
            count = token_repo.revoke_user_tokens(
                user.uuid,
                except_token=current_token
            )
        """
        tokens = self.get_user_tokens(
            user_uuid=user_uuid,
            token_type=token_type,
            include_revoked=False
        )

        count = 0
        now = utc_now()

        for token in tokens:
            # Skip the exception token (current session)
            if except_token and token.token == except_token:
                continue

            self.update(token.uuid, {"revoked_at": now})
            count += 1

        return count

    def revoke_all_except(
        self,
        user_uuid: UUID,
        keep_token: str
    ) -> int:
        """
        Revoke all user tokens except one (close other sessions).

        Alias for revoke_user_tokens with except_token parameter.

        Args:
            user_uuid: The user's UUID
            keep_token: Token to keep active (current session)

        Returns:
            Number of tokens revoked

        Example:
            # "Close other sessions" button
            count = token_repo.revoke_all_except(
                user.uuid,
                keep_token=current_token
            )
        """
        return self.revoke_user_tokens(
            user_uuid=user_uuid,
            except_token=keep_token
        )

    # ====================================================================
    # CLEANUP AND MAINTENANCE
    # ====================================================================

    def cleanup_expired(
        self,
        hard_delete: bool = True,
        older_than_days: int = 7
    ) -> int:
        """
        Delete or soft-delete expired tokens.

        This should be run periodically (cron job) to keep DB clean.

        Args:
            hard_delete: If True, permanently delete. Default: True
            older_than_days: Only delete tokens expired for X days

        Returns:
            Number of tokens deleted

        Example:
            # In a scheduled task (Celery, cron, etc.)
            deleted = token_repo.cleanup_expired()
            logger.info(f"Cleaned up {deleted} expired tokens")
        """
        cutoff_date = utc_now() - timedelta(days=older_than_days)

        # Find expired tokens
        expired_tokens = self.db.query(self.model).filter(
            and_(
                self.model.expires_at < cutoff_date,
                self.model.deleted_at.is_(None)
            )
        ).all()

        count = 0
        for token in expired_tokens:
            if self.delete(token.uuid, hard_delete=hard_delete):
                count += 1

        return count

    def cleanup_revoked(
        self,
        hard_delete: bool = True,
        older_than_days: int = 30
    ) -> int:
        """
        Delete revoked tokens older than X days.

        Args:
            hard_delete: If True, permanently delete
            older_than_days: Only delete tokens revoked X days ago

        Returns:
            Number of tokens deleted

        Example:
            # Monthly cleanup of old revoked tokens
            deleted = token_repo.cleanup_revoked(older_than_days=30)
        """
        cutoff_date = utc_now() - timedelta(days=older_than_days)

        revoked_tokens = self.db.query(self.model).filter(
            and_(
                self.model.revoked_at.isnot(None),
                self.model.revoked_at < cutoff_date,
                self.model.deleted_at.is_(None)
            )
        ).all()

        count = 0
        for token in revoked_tokens:
            if self.delete(token.uuid, hard_delete=hard_delete):
                count += 1

        return count

    # ====================================================================
    # SECURITY AND AUDITING
    # ====================================================================

    def get_suspicious_tokens(
        self,
        user_uuid: UUID,
        current_ip: str
    ) -> List[Token]:
        """
        Find tokens used from different IP addresses.

        Useful for detecting stolen tokens.

        Args:
            user_uuid: The user's UUID
            current_ip: The current IP address

        Returns:
            List of tokens used from different IPs

        Example:
            # In authentication middleware
            suspicious = token_repo.get_suspicious_tokens(user.uuid, request_ip)
            if suspicious:
                # Send alert email
                # Auto-revoke suspicious tokens
                for token in suspicious:
                    token_repo.revoke_token(token.token)
        """
        return self.db.query(self.model).filter(
            and_(
                self.model.user_uuid == user_uuid,
                self.model.revoked_at.is_(None),
                self.model.deleted_at.is_(None),
                self.model.ip_address != current_ip,
                self.model.ip_address.isnot(None)
            )
        ).all()

    def token_exists(self, token: str) -> bool:
        """
        Check if a token exists in database.

        Args:
            token: The token string

        Returns:
            True if exists, False otherwise

        Example:
            if token_repo.token_exists(token_string):
                raise HTTPException(409, "Token already exists")
        """
        query = self.db.query(self.model.uuid).filter(self.model.token == token)
        query = self._apply_soft_delete_filter(query)
        return query.first() is not None
