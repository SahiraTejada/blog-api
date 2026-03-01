"""
Category Routes Module

This module provides API endpoints for category management operations including:
- Create a new category (admin only)
- List all categories (public, paginated)
- Get category by UUID (public)
- Update category (admin only)
- Delete category (admin only)

All endpoints follow REST conventions and return standardized responses.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import AuthContext, require_admin
from app.database.session import get_db
from app.schemas.base import SuccessResponse
from app.schemas.category import (
    CategoryCreateSchema,
    CategoryListRequest,
    CategoryListResponse,
    CategoryResponse,
    CategoryUpdateSchema,
)
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])


# ============================================================================
# CATEGORY CREATION
# ============================================================================


@router.post(
    "/",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new category",
    responses={
        201: {"description": "Category created successfully"},
        401: {"description": "Invalid or missing token"},
        403: {"description": "Admin access required"},
        409: {"description": "Category name already exists"},
        422: {"description": "Validation error"},
    },
)
async def create_category(
    data: CategoryCreateSchema,
    auth: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
) -> CategoryResponse:
    """
    Create a new category.

    Admin-only endpoint.

    - **name**: Unique category name (3-255 characters)
    - **description**: Optional category description

    Requires Authorization header with Bearer token (admin role).
    """
    category_service = CategoryService(db)

    category = category_service.create_category(
        name=data.name,
        description=data.description,
    )

    return CategoryResponse.model_validate(category)


# ============================================================================
# CATEGORY LISTING & LOOKUP
# ============================================================================


@router.get(
    "/",
    response_model=CategoryListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all categories",
    responses={
        200: {"description": "Paginated list of categories"},
    },
)
async def list_categories(
    filters: CategoryListRequest = Depends(),
    db: Session = Depends(get_db),
) -> CategoryListResponse:
    """
    List all categories with optional search and pagination.

    Public endpoint. No authentication required.

    - **search_term**: Searches across category name and description
    """
    category_service = CategoryService(db)

    result = category_service.get_all_categories(
        pagination=filters,
        search_term=filters.search_term,
    )

    return CategoryListResponse(
        data=[CategoryResponse.model_validate(cat) for cat in result.data],
        pagination=result.pagination,
    )


@router.get(
    "/{category_uuid}",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get category by UUID",
    responses={
        200: {"description": "Category details"},
        404: {"description": "Category not found"},
    },
)
async def get_category(
    category_uuid: UUID,
    db: Session = Depends(get_db),
) -> CategoryResponse:
    """
    Get a category by UUID.

    Public endpoint. No authentication required.
    """
    category_service = CategoryService(db)

    category = category_service.get_by_category_uuid(category_uuid)

    return CategoryResponse.model_validate(category)


# ============================================================================
# CATEGORY UPDATE
# ============================================================================


@router.patch(
    "/{category_uuid}",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a category",
    responses={
        200: {"description": "Category updated successfully"},
        401: {"description": "Invalid or missing token"},
        403: {"description": "Admin access required"},
        404: {"description": "Category not found"},
        409: {"description": "Category name already exists"},
        422: {"description": "Validation error"},
    },
)
async def update_category(
    category_uuid: UUID,
    update_data: CategoryUpdateSchema,
    auth: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
) -> CategoryResponse:
    """
    Update a category.

    Admin-only endpoint. Only provided fields will be updated (partial update).

    - **name**: New category name (must be unique)
    - **description**: New category description

    Requires Authorization header with Bearer token (admin role).
    """
    category_service = CategoryService(db)

    updated_category = category_service.update_category(
        category_uuid=category_uuid,
        update_data=update_data.model_dump(exclude_unset=True),
    )

    return CategoryResponse.model_validate(updated_category)


# ============================================================================
# CATEGORY DELETION
# ============================================================================


@router.delete(
    "/{category_uuid}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a category",
    responses={
        200: {"description": "Category deleted successfully"},
        401: {"description": "Invalid or missing token"},
        403: {"description": "Admin access required"},
        404: {"description": "Category not found"},
    },
)
async def delete_category(
    category_uuid: UUID,
    auth: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
) -> SuccessResponse:
    """
    Soft-delete a category.

    Admin-only endpoint. The category data is retained but marked as deleted.

    Requires Authorization header with Bearer token (admin role).
    """
    category_service = CategoryService(db)

    category_service.delete_category(category_uuid)

    return SuccessResponse(message="Category deleted successfully")
