"""
Pagination Utility Module

This module provides standardized pagination functionality for API endpoints.
It helps maintain consistency across all paginated responses and simplifies
the implementation of pagination in route handlers.

Features:
- Automatic page calculation
- Link generation for next/previous pages
- Standardized response format
- Integration with BaseRepository

Author: Blog API Team
Date: 2025-10-20
"""

from math import ceil
from typing import Any, Dict, Generic, List, Optional, TypeVar
from urllib.parse import urlencode

from fastapi import Query, Request
from pydantic import BaseModel, Field

# ============================================================================
# TYPE VARIABLES
# ============================================================================

T = TypeVar("T")
# Generic type variable for paginated items. This allows the pagination
# utility to work with any data type while maintaining type safety.


# ============================================================================
# PAGINATION PARAMETERS
# ============================================================================

class PaginationParams(BaseModel):
    """
    Standard pagination parameters for API endpoints.

    This class defines the common query parameters used for pagination
    across all endpoints. Use it with FastAPI's Depends() to automatically
    validate and parse pagination parameters.

    Attributes:
        page: Current page number (1-indexed)
        page_size: Number of items per page
        skip: Number of items to skip (calculated automatically)

    Example usage in FastAPI:
        @router.get("/users")
        def get_users(
            pagination: PaginationParams = Depends(),
            db: Session = Depends(get_db)
        ):
            users = user_repo.get_multi(
                skip=pagination.skip,
                limit=pagination.page_size
            )
            return paginate(users, pagination, total_count)
    """

    page: int = Field(
        default=1,
        ge=1,
        description="Page number (1-indexed). Must be at least 1."
    )
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of items per page. Must be between 1 and 100."
    )

    @property
    def skip(self) -> int:
        """
        Calculate the number of items to skip for the current page.

        This converts page-based pagination to offset-based pagination
        for database queries.

        Returns:
            Number of items to skip

        Example:
            page=1, page_size=20 -> skip=0
            page=2, page_size=20 -> skip=20
            page=3, page_size=20 -> skip=40
        """
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """
        Get the page size (alias for consistency with repository methods).

        Returns:
            Number of items per page
        """
        return self.page_size

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "page": 1,
                "page_size": 20
            }
        }


def get_pagination_params(
    page: int = Query(
        default=1,
        ge=1,
        description="Page number (1-indexed)"
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Items per page (max 100)"
    )
) -> PaginationParams:
    """
    Dependency function to extract pagination parameters from query strings.

    Use this with FastAPI's Depends() to automatically parse and validate
    pagination parameters from the URL query string.

    Args:
        page: Page number from query parameter
        page_size: Page size from query parameter

    Returns:
        PaginationParams instance with validated parameters

    Example usage:
        @router.get("/items")
        def get_items(
            pagination: PaginationParams = Depends(get_pagination_params),
            db: Session = Depends(get_db)
        ):
            items = item_repo.get_multi(
                skip=pagination.skip,
                limit=pagination.limit
            )
            total = item_repo.count()
            return paginate(items, pagination, total)

    URL examples:
        GET /items?page=1&page_size=20
        GET /items?page=2&page_size=50
        GET /items  (uses defaults: page=1, page_size=20)
    """
    return PaginationParams(page=page, page_size=page_size)


# ============================================================================
# PAGINATION METADATA
# ============================================================================

class PaginationMeta(BaseModel):
    """
    Metadata about the paginated response.

    This provides clients with all the information they need to:
    - Display current page information
    - Calculate total pages
    - Navigate to other pages
    - Show "showing X to Y of Z items"

    Attributes:
        page: Current page number
        page_size: Items per page
        total_items: Total number of items across all pages
        total_pages: Total number of pages
        has_next: Whether there is a next page
        has_previous: Whether there is a previous page
        next_page: Next page number (None if no next page)
        previous_page: Previous page number (None if no previous page)
    """

    page: int = Field(description="Current page number (1-indexed)")
    page_size: int = Field(description="Number of items per page")
    total_items: int = Field(description="Total number of items")
    total_pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_previous: bool = Field(description="Whether there is a previous page")
    next_page: Optional[int] = Field(
        default=None,
        description="Next page number (null if no next page)"
    )
    previous_page: Optional[int] = Field(
        default=None,
        description="Previous page number (null if no previous page)"
    )

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "page": 2,
                "page_size": 20,
                "total_items": 150,
                "total_pages": 8,
                "has_next": True,
                "has_previous": True,
                "next_page": 3,
                "previous_page": 1
            }
        }


class PaginationLinks(BaseModel):
    """
    Navigation links for paginated responses.

    Following REST best practices, this provides hypermedia links that
    clients can use to navigate between pages without constructing URLs.

    Attributes:
        self: Link to the current page
        first: Link to the first page
        last: Link to the last page
        next: Link to the next page (None if no next page)
        previous: Link to the previous page (None if no previous page)
    """

    self: str = Field(description="URL to current page")
    first: str = Field(description="URL to first page")
    last: str = Field(description="URL to last page")
    next: Optional[str] = Field(
        default=None,
        description="URL to next page (null if no next page)"
    )
    previous: Optional[str] = Field(
        default=None,
        description="URL to previous page (null if no previous page)"
    )

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "self": "/api/v1/users?page=2&page_size=20",
                "first": "/api/v1/users?page=1&page_size=20",
                "last": "/api/v1/users?page=8&page_size=20",
                "next": "/api/v1/users?page=3&page_size=20",
                "previous": "/api/v1/users?page=1&page_size=20"
            }
        }


# ============================================================================
# PAGINATED RESPONSE
# ============================================================================

class PaginatedResponse(BaseModel, Generic[T]):
    """
    Standardized paginated response format.

    This generic class provides a consistent structure for all paginated
    API responses. It includes the data, metadata, and navigation links.

    Type Parameters:
        T: The type of items in the data list

    Attributes:
        data: List of items for the current page
        meta: Pagination metadata (counts, page numbers, etc.)
        links: Navigation links (optional, for HATEOAS support)

    Example response:
        {
            "data": [
                {"id": "uuid1", "name": "Item 1"},
                {"id": "uuid2", "name": "Item 2"}
            ],
            "meta": {
                "page": 1,
                "page_size": 20,
                "total_items": 150,
                "total_pages": 8,
                "has_next": true,
                "has_previous": false,
                "next_page": 2,
                "previous_page": null
            },
            "links": {
                "self": "/api/v1/items?page=1&page_size=20",
                "first": "/api/v1/items?page=1&page_size=20",
                "last": "/api/v1/items?page=8&page_size=20",
                "next": "/api/v1/items?page=2&page_size=20",
                "previous": null
            }
        }
    """

    data: List[T] = Field(description="List of items for the current page")
    meta: PaginationMeta = Field(description="Pagination metadata")
    links: Optional[PaginationLinks] = Field(
        default=None,
        description="Navigation links (HATEOAS)"
    )

    class Config:
        """Pydantic model configuration."""
        # Allow arbitrary types for generic typing
        arbitrary_types_allowed = True


# ============================================================================
# PAGINATION HELPERS
# ============================================================================

def calculate_pagination_meta(
    page: int,
    page_size: int,
    total_items: int
) -> PaginationMeta:
    """
    Calculate pagination metadata from page parameters and total count.

    This helper function computes all pagination metadata including
    total pages, navigation flags, and page numbers.

    Args:
        page: Current page number (1-indexed)
        page_size: Number of items per page
        total_items: Total number of items across all pages

    Returns:
        PaginationMeta instance with all calculated fields

    Example:
        meta = calculate_pagination_meta(
            page=2,
            page_size=20,
            total_items=150
        )
        print(f"Page {meta.page} of {meta.total_pages}")
    """
    # Calculate total pages (round up)
    total_pages = ceil(total_items / page_size) if page_size > 0 else 0

    # Ensure we have at least 1 page if there are items
    if total_items > 0 and total_pages == 0:
        total_pages = 1

    # Determine if there are next/previous pages
    has_next = page < total_pages
    has_previous = page > 1

    # Calculate next/previous page numbers
    next_page = page + 1 if has_next else None
    previous_page = page - 1 if has_previous else None

    return PaginationMeta(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
        has_next=has_next,
        has_previous=has_previous,
        next_page=next_page,
        previous_page=previous_page
    )


def build_pagination_links(
    request: Request,
    meta: PaginationMeta,
    query_params: Optional[Dict[str, Any]] = None
) -> PaginationLinks:
    """
    Build navigation links for paginated responses.

    This creates full URLs for pagination navigation, preserving
    any additional query parameters (like filters or search terms).

    Args:
        request: FastAPI Request object to get base URL and path
        meta: Pagination metadata
        query_params: Additional query parameters to preserve

    Returns:
        PaginationLinks instance with all navigation URLs

    Example:
        links = build_pagination_links(
            request=request,
            meta=meta,
            query_params={"status": "active", "search": "john"}
        )
        # URLs will include: ?page=X&page_size=Y&status=active&search=john
    """
    # Get base URL (path without query string)
    base_url = str(request.url).split("?")[0]

    # Prepare query parameters
    params = query_params.copy() if query_params else {}
    params["page_size"] = meta.page_size

    def build_url(page: int) -> str:
        """Helper to build URL with page number."""
        params["page"] = page
        return f"{base_url}?{urlencode(params)}"

    # Build all navigation links
    links = PaginationLinks(
        self=build_url(meta.page),
        first=build_url(1),
        last=build_url(meta.total_pages) if meta.total_pages > 0 else build_url(1),
        next=build_url(meta.next_page) if meta.next_page else None,
        previous=build_url(meta.previous_page) if meta.previous_page else None
    )

    return links


def paginate(
    items: List[T],
    pagination: PaginationParams,
    total_items: int,
    request: Optional[Request] = None,
    query_params: Optional[Dict[str, Any]] = None
) -> PaginatedResponse[T]:
    """
    Create a paginated response from a list of items.

    This is the main helper function you'll use in your route handlers
    to convert a list of items into a standardized paginated response.

    Args:
        items: List of items for the current page
        pagination: Pagination parameters (page, page_size)
        total_items: Total count of items across all pages
        request: Optional FastAPI Request for generating links
        query_params: Optional additional query parameters to preserve

    Returns:
        PaginatedResponse with data, metadata, and optional links

    Example usage in route:
        @router.get("/users", response_model=PaginatedResponse[UserSchema])
        def get_users(
            request: Request,
            pagination: PaginationParams = Depends(get_pagination_params),
            status: str = Query(None),
            db: Session = Depends(get_db)
        ):
            # Get paginated data
            users = user_repo.get_multi(
                skip=pagination.skip,
                limit=pagination.limit,
                filters={"status": status} if status else None
            )

            # Get total count
            total = user_repo.count(filters={"status": status} if status else None)

            # Return paginated response
            return paginate(
                items=users,
                pagination=pagination,
                total_items=total,
                request=request,
                query_params={"status": status} if status else None
            )
    """
    # Calculate pagination metadata
    meta = calculate_pagination_meta(
        page=pagination.page,
        page_size=pagination.page_size,
        total_items=total_items
    )

    # Build navigation links if request is provided
    links = None
    if request:
        links = build_pagination_links(request, meta, query_params)

    return PaginatedResponse(
        data=items,
        meta=meta,
        links=links
    )


def paginate_from_repository(
    repository: Any,
    pagination: PaginationParams,
    request: Optional[Request] = None,
    filters: Optional[Dict[str, Any]] = None,
    order_by: Optional[str] = None,
    order_desc: bool = False,
    include_deleted: bool = False,
    query_params: Optional[Dict[str, Any]] = None
) -> PaginatedResponse[T]:
    """
    Paginate directly from a repository with automatic count query.

    This convenience function combines the repository query and count
    into a single helper, reducing boilerplate in route handlers.

    Args:
        repository: Instance of BaseRepository or its subclass
        pagination: Pagination parameters
        request: Optional FastAPI Request for generating links
        filters: Optional filters to pass to repository
        order_by: Optional field name to sort by
        order_desc: If True, sorts in descending order
        include_deleted: If True, includes soft-deleted records
        query_params: Optional additional query parameters for links

    Returns:
        PaginatedResponse with data and metadata

    Example usage:
        @router.get("/users", response_model=PaginatedResponse[UserSchema])
        def get_users(
            request: Request,
            pagination: PaginationParams = Depends(get_pagination_params),
            status: str = Query(None),
            db: Session = Depends(get_db)
        ):
            user_repo = UserRepository(db)

            return paginate_from_repository(
                repository=user_repo,
                pagination=pagination,
                request=request,
                filters={"status": status} if status else None,
                order_by="created_at",
                order_desc=True,
                query_params={"status": status} if status else None
            )

    Note:
        This makes two database queries: one for data, one for count.
        For better performance with large datasets, consider caching the count.
    """
    # Get paginated items
    items = repository.get_multi(
        skip=pagination.skip,
        limit=pagination.limit,
        include_deleted=include_deleted,
        filters=filters,
        order_by=order_by,
        order_desc=order_desc
    )

    # Get total count
    total = repository.count(
        include_deleted=include_deleted,
        filters=filters
    )

    # Return paginated response
    return paginate(
        items=items,
        pagination=pagination,
        total_items=total,
        request=request,
        query_params=query_params
    )


# ============================================================================
# CURSOR-BASED PAGINATION (ADVANCED)
# ============================================================================

class CursorPaginationParams(BaseModel):
    """
    Parameters for cursor-based pagination.

    Cursor-based pagination is more efficient for large datasets and
    real-time data. Instead of page numbers, it uses a cursor (usually
    a timestamp or ID) to mark the position in the result set.

    Advantages over page-based pagination:
    - No "page drift" when data is added/removed
    - More efficient for large offsets
    - Better for infinite scroll UIs
    - Consistent results even as data changes

    Attributes:
        cursor: The cursor value (timestamp or ID of last seen item)
        limit: Number of items to return
        direction: Direction to paginate (forward or backward)

    Example:
        # First request (no cursor)
        GET /items?limit=20

        # Next request (using last item's cursor)
        GET /items?cursor=2025-01-15T10:30:00Z&limit=20
    """

    cursor: Optional[str] = Field(
        default=None,
        description="Cursor value (timestamp or ID) for pagination"
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of items to return"
    )
    direction: str = Field(
        default="forward",
        description="Pagination direction (forward or backward)"
    )

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "cursor": "2025-01-15T10:30:00Z",
                "limit": 20,
                "direction": "forward"
            }
        }


# ============================================================================
# USAGE EXAMPLES
# ============================================================================
"""
COMPLETE USAGE EXAMPLE IN FASTAPI ROUTE:

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.repositories import UserRepository
from app.schemas.user import UserResponse
from app.utils.pagination import (
    PaginatedResponse,
    PaginationParams,
    get_pagination_params,
    paginate,
    paginate_from_repository
)

router = APIRouter()

# METHOD 1: Manual pagination (more control)
@router.get("/users/manual", response_model=PaginatedResponse[UserResponse])
def get_users_manual(
    request: Request,
    pagination: PaginationParams = Depends(get_pagination_params),
    status: str = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    user_repo = UserRepository(db)

    # Get filtered and paginated users
    filters = {"status": status} if status else None
    users = user_repo.get_multi(
        skip=pagination.skip,
        limit=pagination.limit,
        filters=filters,
        order_by="created_at",
        order_desc=True
    )

    # Get total count for pagination
    total = user_repo.count(filters=filters)

    # Build query params for links
    query_params = {"status": status} if status else None

    # Return paginated response
    return paginate(
        items=users,
        pagination=pagination,
        total_items=total,
        request=request,
        query_params=query_params
    )


# METHOD 2: Automatic pagination (less boilerplate)
@router.get("/users/auto", response_model=PaginatedResponse[UserResponse])
def get_users_auto(
    request: Request,
    pagination: PaginationParams = Depends(get_pagination_params),
    status: str = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    user_repo = UserRepository(db)

    return paginate_from_repository(
        repository=user_repo,
        pagination=pagination,
        request=request,
        filters={"status": status} if status else None,
        order_by="created_at",
        order_desc=True,
        query_params={"status": status} if status else None
    )


# EXAMPLE: Pagination with search
@router.get("/users/search", response_model=PaginatedResponse[UserResponse])
def search_users(
    request: Request,
    q: str = Query(..., description="Search query"),
    pagination: PaginationParams = Depends(get_pagination_params),
    db: Session = Depends(get_db)
):
    user_repo = UserRepository(db)

    # Use repository's search method
    users = user_repo.search(
        search_fields=["name", "email"],
        search_term=q,
        skip=pagination.skip,
        limit=pagination.limit
    )

    # For search, we need a separate count
    # (BaseRepository doesn't have search_count, so we approximate)
    total = len(users)  # Or implement a proper search count method

    return paginate(
        items=users,
        pagination=pagination,
        total_items=total,
        request=request,
        query_params={"q": q}
    )
"""
