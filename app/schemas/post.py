from app.schemas.base import BaseModelSchema
from app.models.posts import PostStatus
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Dict, Generic, List, Optional, TypeVar

class PostBaseSchema(BaseModelSchema):
    author_uuid: UUID = Field(
        description="Unique identifier (UUID) for the author of the post", json_schema_extra={"example": "123e4567-e89b-12d3-a456-426614174000"}
    )
    title : str = Field(
        min_length=1, max_length=255, description="User's first name", json_schema_extra={"example": "John"}
    )
    content: str = Field(
        min_length=1, description="Content of the post", json_schema_extra={"example": "This is the content of the blog post."}
    )
    status: PostStatus


    category_ids: List[str] = []
