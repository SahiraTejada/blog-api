"""
User Routes Module

This module provides API endpoints for user management operations including:
- Get current user profile
- Update current user profile
- Delete own account
- Get user by UUID (public profile)
- List all users (admin only, paginated)

All endpoints follow REST conventions and return standardized responses.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import AuthContext, get_auth_context, require_admin
from app.database.session import get_db
from app.schemas.base import SuccessResponse
from app.schemas.user import UserBaseSchema, UserListRequest, UserListResponse, UserPublicSchema, UserUpdateSchema
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


# ============================================================================
# CURRENT USER (ME)
# ============================================================================


@router.get(
    "/me",
    response_model=UserBaseSchema,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    responses={
        200: {"description": "Current user profile"},
        401: {"description": "Invalid or missing token"},
    },
)
async def get_me(
    auth: AuthContext = Depends(get_auth_context),
) -> UserBaseSchema:
    """
    Get the authenticated user's profile.

    Returns full user information including email and role.

    Requires Authorization header with Bearer token.
    """
    return UserBaseSchema.model_validate(auth.user)


@router.patch(
    "/me",
    response_model=UserBaseSchema,
    status_code=status.HTTP_200_OK,
    summary="Update current user profile",
    responses={
        200: {"description": "Profile updated successfully"},
        401: {"description": "Invalid or missing token"},
        409: {"description": "Username or email already exists"},
        422: {"description": "Validation error"},
    },
)
async def update_me(
    update_data: UserUpdateSchema,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> UserBaseSchema:
    """
    Update the authenticated user's profile.

    Only provided fields will be updated (partial update).

    - **username**: New username (3-50 characters)
    - **email**: New email address
    - **first_name**: New first name
    - **last_name**: New last name

    Requires Authorization header with Bearer token.
    """
    user_service = UserService(db)

    updated_user = user_service.update_user(
        user_uuid=auth.user.uuid,
        update_data=update_data.model_dump(exclude_unset=True),
    )

    return UserBaseSchema.model_validate(updated_user)


@router.delete(
    "/me",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete own account",
    responses={
        200: {"description": "Account deleted successfully"},
        401: {"description": "Invalid or missing token"},
    },
)
async def delete_me(
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> SuccessResponse:
    """
    Soft-delete the authenticated user's account.

    This deactivates the account. The user data is retained
    but the account can no longer be used to authenticate.

    Requires Authorization header with Bearer token.
    """
    user_service = UserService(db)

    user_service.delete_user(auth.user.uuid)

    return SuccessResponse(message="Account deleted successfully")


# ============================================================================
# USER LOOKUP
# ============================================================================


@router.get(
    "/{user_uuid}",
    response_model=UserPublicSchema,
    status_code=status.HTTP_200_OK,
    summary="Get user public profile",
    responses={
        200: {"description": "User public profile"},
        404: {"description": "User not found"},
    },
)
async def get_user_by_uuid(
    user_uuid: UUID,
    db: Session = Depends(get_db),
) -> UserPublicSchema:
    """
    Get a user's public profile by UUID.

    Returns limited user information (no email or role).
    This endpoint is public and does not require authentication.
    """
    user_service = UserService(db)

    user = user_service.get_by_user_uuid(user_uuid)

    return UserPublicSchema.model_validate(user)


# ============================================================================
# ADMIN: USER LISTING
# ============================================================================


@router.get(
    "/",
    response_model=UserListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all users",
    responses={
        200: {"description": "Paginated list of users"},
        401: {"description": "Invalid or missing token"},
        403: {"description": "Admin access required"},
    },
)
async def list_users(
    auth: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
    filters: UserListRequest = Depends(),
) -> UserListResponse:
    """
    List all users with optional filtering and pagination.

    Admin-only endpoint. Supports filtering by role and text search.

    - **search_term**: Searches across username, email, first_name, and last_name

    Requires Authorization header with Bearer token (admin role).
    """
    user_service = UserService(db)

    result = user_service.get_all_users(
        pagination=filters,
        role=filters.role,
        search_term=filters.search_term,
    )

    return UserListResponse(
        data=[UserBaseSchema.model_validate(user) for user in result.data],
        pagination=result.pagination,
    )
