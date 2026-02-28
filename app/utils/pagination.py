from math import ceil
from typing import List, TypeVar

from app.schemas.base import PaginatedResponse, PaginationMeta, PaginationParams

T = TypeVar("T")


def paginate(
    items: List[T],
    pagination: PaginationParams,
    total_items: int
) -> PaginatedResponse[T]:
    """
    Create a paginated response with items and pagination metadata.

    This function takes a list of items, pagination parameters, and a total count,
    and returns a properly formatted paginated response with all metadata.

    Args:
        items: List of items for the current page
        pagination: PaginationParams with page and page_size
        total_items: Total number of items across all pages

    Returns:
        PaginatedResponse with data and pagination metadata
    """
    # Calculate total pages
    total_pages = ceil(total_items / pagination.page_size) if pagination.page_size > 0 else 0

    # Determine if there are next/previous pages
    has_next = pagination.page < total_pages
    has_previous = pagination.page > 1

    # Calculate next and previous page numbers
    next_page = pagination.page + 1 if has_next else None
    previous_page = pagination.page - 1 if has_previous else None

    meta = PaginationMeta(
        page=pagination.page,
        page_size=pagination.page_size,
        total_items=total_items,
        total_pages=total_pages,
        has_next=has_next,
        has_previous=has_previous,
        next_page=next_page,
        previous_page=previous_page
    )

    return PaginatedResponse(
        data=items,
        pagination=meta
    )


def create_pagination_meta(
    page: int,
    page_size: int,
    total_items: int
) -> PaginationMeta:
    """
    Create pagination metadata from raw parameters.

    This is a lower-level function that creates PaginationMeta directly
    without requiring PaginationParams. Useful for custom pagination scenarios.

    Args:
        page: Current page number (1-indexed)
        page_size: Number of items per page
        total_items: Total number of items

    Returns:
        PaginationMeta with calculated pagination information

    Example:
        meta = create_pagination_meta(page=2, page_size=20, total_items=100)
    """
    # Calculate total pages
    total_pages = ceil(total_items / page_size) if page_size > 0 else 0

    # Determine if there are next/previous pages
    has_next = page < total_pages
    has_previous = page > 1

    # Calculate next and previous page numbers
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
