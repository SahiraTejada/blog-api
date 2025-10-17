from sqlalchemy import Column, String, Table, ForeignKey, Text
from app.models.base import BaseModel
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID


post_categories = Table(
    'post_categories',
    BaseModel.metadata,
    Column('post_uuid', UUID(as_uuid=True), ForeignKey('posts.uuid'), primary_key=True),
    Column('category_uuid', UUID(as_uuid=True), ForeignKey('categories.uuid'), primary_key=True)
)

class Category(BaseModel):

    __tablename__ = "categories"

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    # Relationships
    posts = relationship(
        "Post",
        secondary=post_categories,
        back_populates="categories"
    )

    def __repr__(self) -> str:
        """Return string representation of the model."""
        return f"<{self.__class__.__name__}(name={self.name})>"
