from typing import List, Optional

from pydantic import Field

from app.schemas.base import (
    BaseSchema,
    PaginatedResponse,
    PaginationMeta,
    PaginationParams,
    ResponseSchema,
    UpdateSchema,
)


class CategoryBaseSchema(BaseSchema):
    """
    Base schema with common category fields.

    Defines the core fields and validations shared across category schemas.

    """

    name: str = Field(
        min_length=3,
        max_length=255,
        description="Category name (must be unique)",
        json_schema_extra={"example": "Technology"},
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional description for the category",
        json_schema_extra={"example": "Posts about technology and programming"},
    )


class CategoryCreateSchema(CategoryBaseSchema):
    """
    Schema for creating a new category.

    """

    pass


class CategoryUpdateSchema(UpdateSchema):
    """
    Schema for updating an existing category.

    All fields are optional to support partial updates (PATCH).
    Only provided fields will be updated.

    """

    name: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=255,
        description="New category name (must be unique)",
        json_schema_extra={"example": "Tech & Programming"},
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="New category description",
        json_schema_extra={"example": "Updated description for technology posts"},
    )


class CategoryResponse(CategoryBaseSchema, ResponseSchema):
    """
    Schema for category response.

    Combines CategoryBaseSchema fields with ResponseSchema (UUID + timestamps).

    Attributes:
        uuid: Unique identifier (from ResponseSchema)
        name: Category name (from CategoryBaseSchema)
        description: Category description (from CategoryBaseSchema)
        created_at, updated_at, deleted_at: Timestamps (from ResponseSchema)
    """

    model_config = {
        "json_schema_extra": {
            "example": {
                "uuid": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Technology",
                "description": "Posts about technology and programming",
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T14:20:00Z",
                "deleted_at": None,
            }
        }
    }


class CategoryWithPostCountResponse(CategoryResponse):
    """
    Schema for category response including post count.

    Used when returning categories with statistics.
    """

    post_count: int = Field(
        description="Number of posts in this category",
        json_schema_extra={"example": 42},
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "uuid": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Technology",
                "description": "Posts about technology and programming",
                "post_count": 42,
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T14:20:00Z",
                "deleted_at": None,
            }
        }
    }

class CategoryListRequest(PaginationParams):
    """
    Request schema for listing categories with pagination and search.
    """

    search_term: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Optional search term to filter categories by name",
        json_schema_extra={"example": "tech"},
    )

class CategoryListResponse(PaginatedResponse[CategoryResponse]):
    """
    Schema for paginated list of categories.

    Used as response for get_all_categories endpoint.

    Attributes:
        data: List of categories for the current page
        pagination: Pagination metadata (page, total_items, etc.)
    """

    data: List[CategoryResponse] = Field(description="List of categories for the current page")
    pagination: PaginationMeta = Field(description="Pagination metadata")

    model_config = {
        "json_schema_extra": {
            "example": {
                "data": [
                    {
                        "uuid": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Technology",
                        "description": "Posts about technology",
                        "created_at": "2025-01-15T10:30:00Z",
                        "updated_at": "2025-01-15T14:20:00Z",
                        "deleted_at": None,
                    },
                    {
                        "uuid": "223e4567-e89b-12d3-a456-426614174001",
                        "name": "Programming",
                        "description": "Coding tutorials and tips",
                        "created_at": "2025-01-16T08:00:00Z",
                        "updated_at": "2025-01-16T08:00:00Z",
                        "deleted_at": None,
                    },
                ],
                "pagination": {
                    "page": 1,
                    "page_size": 20,
                    "total_items": 50,
                    "total_pages": 3,
                    "has_next": True,
                    "has_previous": False,
                    "next_page": 2,
                    "previous_page": None,
                },
            }
        }
    }
