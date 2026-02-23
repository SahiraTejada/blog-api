"""
Authentication Routes Module

This module provides API endpoints for authentication operations including:
- User registration
- Login (with token generation)
- Token refresh
- Logout (single and all devices)
- Session management
- Password change

All endpoints follow REST conventions and return standardized responses.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException, TokenMissingException, UserNotFoundException
from app.database.session import get_db
from app.models.tokens import TokenType
from app.models.users import UserRole
from app.schemas.auth import AuthResponseSchema, LoginUserSchema, RegisterUserSchema, UserPasswordUpdateSchema
from app.schemas.token import (
    ActiveSessionsResponseSchema,
    RefreshTokenResponseSchema,
    RevokeTokensResponseSchema,
    TokenSessionSchema,
)
from app.schemas.user import UserBaseSchema
from app.services.auth_service import AuthService
from app.services.token_service import TokenService

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_client_ip(request: Request) -> Optional[str]:
    """
    Extract client IP address from request.

    Checks X-Forwarded-For header for proxied requests,
    falls back to direct client host.

    Args:
        request: FastAPI Request object

    Returns:
        Client IP address or None
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For can contain multiple IPs, first is the client
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def get_bearer_token(request: Request) -> str:
    """
    Extract bearer token from Authorization header.

    Args:
        request: FastAPI Request object

    Returns:
        Token string without "Bearer " prefix

    Raises:
        TokenMissingException: If no Authorization header
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise TokenMissingException()
    return auth_header.replace("Bearer ", "")


# ============================================================================
# REGISTRATION
# ============================================================================


@router.post(
    "/register",
    response_model=AuthResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    responses={
        201: {"description": "User created and logged in successfully"},
        409: {"description": "Username or email already exists"},
        422: {"description": "Validation error"},
    },
)
async def register(
    user_data: RegisterUserSchema,
    request: Request,
    db: Session = Depends(get_db),
) -> AuthResponseSchema:
    """
    Register a new user account and return tokens.

    Creates a new user and automatically logs them in by returning
    access and refresh tokens. No separate login required.

    - **username**: Unique username (3-50 characters)
    - **email**: Valid unique email address
    - **password**: Password (min 8 characters)
    - **first_name**: User's first name
    - **last_name**: User's last name
    """
    auth_service = AuthService(db)
    token_service = TokenService(db)

    # Create user
    user = auth_service.create_user(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=user_data.role if user_data.role else UserRole.USER,
    )

    # Get client IP for token tracking
    ip_address = get_client_ip(request)

    # Create token pair (auto-login)
    tokens = token_service.create_token_pair(
        user_uuid=user.uuid,
        ip_address=ip_address,
    )

    return AuthResponseSchema(
        access_token=tokens["access"].token,
        refresh_token=tokens["refresh"].token,
        user=UserBaseSchema.model_validate(user),
    )


# ============================================================================
# LOGIN / LOGOUT
# ============================================================================


@router.post(
    "/login",
    response_model=AuthResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Login and get tokens",
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials"},
    },
)
async def login(
    credentials: LoginUserSchema,
    request: Request,
    db: Session = Depends(get_db),
) -> AuthResponseSchema:
    """
    Authenticate user and return access/refresh tokens.

    Validates credentials and returns a token pair for API authentication.
    The access token is short-lived, use the refresh token to get new ones.

    - **email**: User's email address
    - **password**: User's password
    """
    auth_service = AuthService(db)
    token_service = TokenService(db)

    # Validate credentials
    user = auth_service.login(
        email=credentials.email,
        password=credentials.password,
    )

    # Get client IP for token tracking
    ip_address = get_client_ip(request)

    # Create token pair
    tokens = token_service.create_token_pair(
        user_uuid=user.uuid,
        ip_address=ip_address,
    )

    return AuthResponseSchema(
        access_token=tokens["access"].token,
        refresh_token=tokens["refresh"].token,
        user=UserBaseSchema.model_validate(user),
    )


@router.post(
    "/logout",
    response_model=RevokeTokensResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Logout current session",
    responses={
        200: {"description": "Logged out successfully"},
        401: {"description": "Invalid or missing token"},
    },
)
async def logout(
    request: Request,
    db: Session = Depends(get_db),
) -> RevokeTokensResponseSchema:
    """
    Logout from current session.

    Revokes the current access token. The user will need to
    login again to get new tokens.

    Requires Authorization header with Bearer token.
    """
    token_service = TokenService(db)
    token_string = get_bearer_token(request)

    # Validate token first (raises exception if invalid)
    token_service.validate_access_token(token_string)

    # Revoke the token
    revoked = token_service.revoke_token(token_string)

    return RevokeTokensResponseSchema(
        message="Logged out successfully",
        revoked_count=1 if revoked else 0,
    )


@router.post(
    "/logout-all",
    response_model=RevokeTokensResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Logout from all devices",
    responses={
        200: {"description": "Logged out from all devices"},
        401: {"description": "Invalid or missing token"},
    },
)
async def logout_all(
    request: Request,
    db: Session = Depends(get_db),
) -> RevokeTokensResponseSchema:
    """
    Logout from all devices.

    Revokes all tokens for the current user, effectively logging
    out from all devices and sessions.

    Requires Authorization header with Bearer token.
    """
    token_service = TokenService(db)
    token_string = get_bearer_token(request)

    # Validate and get user from token
    token = token_service.validate_access_token(token_string)

    # Revoke all user tokens
    count = token_service.revoke_all_user_tokens(token.user_uuid)

    return RevokeTokensResponseSchema(
        message=f"Logged out from {count} devices",
        revoked_count=count,
    )


# ============================================================================
# TOKEN REFRESH
# ============================================================================


@router.post(
    "/refresh",
    response_model=RefreshTokenResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    responses={
        200: {"description": "New tokens generated"},
        401: {"description": "Invalid or expired refresh token"},
    },
)
async def refresh_token(
    request: Request,
    db: Session = Depends(get_db),
) -> RefreshTokenResponseSchema:
    """
    Get new access token using refresh token.

    Uses the refresh token from Authorization header to generate
    a new access token (and rotated refresh token).

    The old refresh token is revoked for security.

    Requires Authorization header with Bearer refresh_token.
    """
    token_service = TokenService(db)
    refresh_token_string = get_bearer_token(request)
    ip_address = get_client_ip(request)

    # Refresh tokens (validates, revokes old, creates new)
    new_tokens = token_service.refresh_tokens(
        refresh_token_string=refresh_token_string,
        ip_address=ip_address,
        rotate_refresh_token=True,
    )

    return RefreshTokenResponseSchema(
        access_token=new_tokens["access"].token,
        refresh_token=new_tokens["refresh"].token if "refresh" in new_tokens else None,
    )


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================


@router.get(
    "/sessions",
    response_model=ActiveSessionsResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Get active sessions",
    responses={
        200: {"description": "List of active sessions"},
        401: {"description": "Invalid or missing token"},
    },
)
async def get_sessions(
    request: Request,
    db: Session = Depends(get_db),
) -> ActiveSessionsResponseSchema:
    """
    Get all active sessions for current user.

    Returns a list of all active access tokens/sessions,
    including IP address and creation time.

    The current session is marked with is_current=True.

    Requires Authorization header with Bearer token.
    """
    token_service = TokenService(db)
    current_token_string = get_bearer_token(request)

    # Validate and get user
    current_token = token_service.validate_access_token(current_token_string)

    # Get all active access tokens
    tokens = token_service.get_user_tokens(
        user_uuid=current_token.user_uuid,
        token_type=TokenType.ACCESS,
        include_revoked=False,
        include_expired=False,
    )

    # Build session list
    sessions = [
        TokenSessionSchema(
            uuid=t.uuid,
            type=t.type,
            created_at=t.created_at,
            expires_at=t.expires_at,
            ip_address=t.ip_address,
            is_current=(t.token == current_token_string),
        )
        for t in tokens
    ]

    return ActiveSessionsResponseSchema(
        sessions=sessions,
        total=len(sessions),
    )


@router.delete(
    "/sessions/{session_uuid}",
    response_model=RevokeTokensResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Revoke a specific session",
    responses={
        200: {"description": "Session revoked"},
        401: {"description": "Invalid or missing token"},
        404: {"description": "Session not found"},
    },
)
async def revoke_session(
    session_uuid: str,
    request: Request,
    db: Session = Depends(get_db),
) -> RevokeTokensResponseSchema:
    """
    Revoke a specific session by UUID.

    Allows users to remotely logout from a specific device/session.

    Requires Authorization header with Bearer token.
    """
    token_service = TokenService(db)
    current_token_string = get_bearer_token(request)

    # Validate current token
    current_token = token_service.validate_access_token(current_token_string)

    # Get the session token to revoke
    session_token = token_service.get_by_uuid(UUID(session_uuid))

    # Ensure the token belongs to the current user
    if session_token.user_uuid != current_token.user_uuid:
        raise ForbiddenException(message="Cannot revoke another user's session")

    # Revoke the session
    token_service.revoke_token(session_token.token)

    return RevokeTokensResponseSchema(
        message="Session revoked successfully",
        revoked_count=1,
    )


@router.post(
    "/logout-others",
    response_model=RevokeTokensResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Logout from other devices",
    responses={
        200: {"description": "Logged out from other devices"},
        401: {"description": "Invalid or missing token"},
    },
)
async def logout_others(
    request: Request,
    db: Session = Depends(get_db),
) -> RevokeTokensResponseSchema:
    """
    Logout from all other devices except current.

    Revokes all tokens except the current one, keeping
    only the current session active.

    Requires Authorization header with Bearer token.
    """
    token_service = TokenService(db)
    current_token_string = get_bearer_token(request)

    # Validate current token
    current_token = token_service.validate_access_token(current_token_string)

    # Revoke all except current
    count = token_service.revoke_all_except_current(
        user_uuid=current_token.user_uuid,
        current_token=current_token_string,
    )

    return RevokeTokensResponseSchema(
        message=f"Logged out from {count} other devices",
        revoked_count=count,
    )


# ============================================================================
# PASSWORD MANAGEMENT
# ============================================================================


@router.post(
    "/change-password",
    response_model=RevokeTokensResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Change password",
    responses={
        200: {"description": "Password changed successfully"},
        401: {"description": "Invalid current password or token"},
    },
)
async def change_password(
    password_data: UserPasswordUpdateSchema,
    request: Request,
    db: Session = Depends(get_db),
) -> RevokeTokensResponseSchema:
    """
    Change current user's password.

    Requires current password verification. After changing password,
    all other sessions are revoked for security.

    - **current_password**: Current password for verification
    - **new_password**: New password (min 8 characters)

    Requires Authorization header with Bearer token.
    """
    auth_service = AuthService(db)
    token_service = TokenService(db)
    current_token_string = get_bearer_token(request)

    # Validate current token and get user
    current_token = token_service.validate_access_token(current_token_string)

    # Get user from repository
    user = auth_service.user_repo.get_by_uuid(current_token.user_uuid)
    if not user:
        raise UserNotFoundException(identifier=str(current_token.user_uuid))

    # Change password (validates current password)
    auth_service.change_password(
        user=user,
        current_password=password_data.current_password,
        new_password=password_data.new_password,
    )

    # Revoke all other sessions for security
    count = token_service.revoke_all_except_current(
        user_uuid=current_token.user_uuid,
        current_token=current_token_string,
    )

    return RevokeTokensResponseSchema(
        message=f"Password changed. Logged out from {count} other devices.",
        revoked_count=count,
    )
