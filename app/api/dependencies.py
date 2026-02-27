"""
API Dependencies Module

This module provides FastAPI dependencies for authentication and authorization.
Dependencies are composable functions used with Depends() to inject
authenticated context into route handlers.

Architecture (Proposal 5 — Hybrid: AuthContext + Router-Level):

    get_bearer_token() -> extracts JWT string from Authorization header
    get_auth_context() -> validates token + loads User -> returns AuthContext
    RoleChecker       -> verifies user role -> returns AuthContext

Usage:
    # Protected endpoint (any authenticated user)
    @router.post("/posts")
    async def create_post(auth: AuthContext = Depends(get_auth_context)):
        auth.user   # User model
        auth.token  # JWT string

    # Admin-only endpoint
    @router.post("/categories")
    async def create_category(auth: AuthContext = Depends(require_admin)):
        auth.user   # Admin user

    # Token-only endpoint (e.g., refresh with a refresh token)
    @router.post("/auth/refresh")
    async def refresh(token: str = Depends(get_bearer_token)):
        ...
"""

from dataclasses import dataclass
from typing import List, Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import (
    ForbiddenException,
    TokenMissingException,
    UserNotFoundException,
)
from app.database.session import get_db
from app.models.users import User, UserRole
from app.repositories.user_repository import UserRepository
from app.services.token_service import TokenService


# ============================================================================
# AUTH CONTEXT
# ============================================================================


@dataclass(frozen=True)
class AuthContext:
    """
    Authenticated request context.

    Bundles the validated User model and raw JWT token string
    into a single immutable object. This is the return type of
    get_auth_context() and RoleChecker.

    Attributes:
        user: The authenticated, active User model
        token: The raw JWT string (for revocation, session identification)
    """

    user: User
    token: str


# ============================================================================
# SECURITY SCHEME
# ============================================================================

# HTTPBearer integrates with OpenAPI/Swagger UI automatically.
# auto_error=False lets us handle missing tokens with our own exceptions
# instead of FastAPI's generic 403.
security_scheme = HTTPBearer(auto_error=False)


# ============================================================================
# TOKEN EXTRACTION
# ============================================================================


def get_bearer_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> str:
    """
    Extract bearer token from Authorization header.

    Uses FastAPI's HTTPBearer which:
    - Validates "Bearer" scheme
    - Extracts token string
    - Adds lock icon to Swagger UI

    This dependency exists separately for endpoints that only need
    the raw token without full user authentication (e.g., /auth/refresh
    which receives a refresh token, not an access token).

    Args:
        credentials: Auto-injected by HTTPBearer security scheme

    Returns:
        Token string (without "Bearer " prefix)

    Raises:
        TokenMissingException: If no Authorization header or invalid scheme
    """
    if not credentials:
        raise TokenMissingException()
    return credentials.credentials


# ============================================================================
# AUTH CONTEXT (SINGLE DEPENDENCY FOR PROTECTED ENDPOINTS)
# ============================================================================


def get_auth_context(
    token: str = Depends(get_bearer_token),
    db: Session = Depends(get_db),
) -> AuthContext:
    """
    Validate access token, load user, and return AuthContext.

    This is the single dependency for all protected endpoints.
    It performs the full authentication flow:
    1. Decode and verify JWT signature
    2. Check token exists in DB and is not revoked/expired
    3. Load User model from database
    4. Verify user is active (not soft-deleted)

    FastAPI caches Depends(get_db) per request, so both this
    dependency and the route handler share the same DB session.

    Args:
        token: JWT string from get_bearer_token
        db: Database session from get_db (shared with route handler)

    Returns:
        AuthContext: Immutable object with .user and .token

    Raises:
        TokenExpiredException: Token has expired
        TokenInvalidException: Token signature invalid or malformed
        TokenNotFoundException: Token not in DB or revoked
        UserNotFoundException: User referenced by token no longer exists
        ForbiddenException: User account has been deactivated (soft-deleted)
    """
    token_service = TokenService(db)
    user_repo = UserRepository(db)

    # Validate JWT signature + check DB (not revoked, not expired)
    validated_token = token_service.validate_access_token(token)

    # Load user from database
    user = user_repo.get_by_uuid(validated_token.user_uuid)
    if not user:
        raise UserNotFoundException(identifier=str(validated_token.user_uuid))

    # Check soft-delete
    if user.deleted_at is not None:
        raise ForbiddenException(message="User account has been deactivated")

    return AuthContext(user=user, token=token)


# ============================================================================
# ROLE-BASED ACCESS CONTROL
# ============================================================================


class RoleChecker:
    """
    Dependency class for role-based access control.

    Uses a callable class pattern so it works with FastAPI's Depends().
    Returns AuthContext (same type as get_auth_context) for consistency.

    Usage in routes:
        @router.post("/categories")
        async def create_category(
            auth: AuthContext = Depends(require_admin),
        ):
            ...
    """

    def __init__(self, allowed_roles: List[UserRole]):
        """
        Initialize with list of allowed roles.

        Args:
            allowed_roles: Roles that are permitted to access the endpoint
        """
        self.allowed_roles = allowed_roles

    def __call__(
        self,
        auth: AuthContext = Depends(get_auth_context),
    ) -> AuthContext:
        """
        Check if user's role is in the allowed list.

        Args:
            auth: AuthContext from get_auth_context

        Returns:
            AuthContext: The same AuthContext if authorized

        Raises:
            ForbiddenException: If user's role is not in allowed_roles
        """
        if auth.user.role not in self.allowed_roles:
            raise ForbiddenException(
                message="You do not have permission to perform this action"
            )
        return auth


# ============================================================================
# PRE-BUILT ROLE DEPENDENCIES
# ============================================================================

# Any authenticated active user (USER or ADMIN)
require_user = RoleChecker([UserRole.USER, UserRole.ADMIN])

# Admin only
require_admin = RoleChecker([UserRole.ADMIN])
