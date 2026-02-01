from datetime import datetime, timezone
from typing import Optional, TypeVar
from uuid import UUID as UUID_TYPE
from uuid import uuid4

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class BaseModel(Base):
    """
    Base model with common fields for all models.

    Using SQLAlchemy 2.0 style with Mapped annotations.
    """

    __abstract__ = True

    uuid: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        unique=True,
        index=True,
        default=uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None
    )

    def __repr__(self) -> str:
        """Return string representation of the model."""
        return f"<{self.__class__.__name__}(uuid={self.uuid})>"


# ============================================================================
# TYPE VARIABLES
# ============================================================================
# TypeVar allows us to create generic classes that work with any model type.
# This enables type safety while maintaining flexibility.

ModelType = TypeVar("ModelType", bound=BaseModel)
# ModelType is bound to BaseModel, meaning it must be a subclass of BaseModel.
# This ensures our repository only works with valid database models.
