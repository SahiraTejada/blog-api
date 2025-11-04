import enum
from typing import TYPE_CHECKING, List

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.comments import Comments
    from app.models.follows import Follow
    from app.models.likes import Likes
    from app.models.posts import Post
    from app.models.tokens import Token


class UserRole(enum.Enum):
    """
    User roles for access control.

    - USER: Regular authenticated user (default)
    - ADMIN: Administrator with full access

    Note: GUEST users are unauthenticated visitors (no database row).
    """
    USER = "USER"
    ADMIN = "ADMIN"


class User(BaseModel):
    """
    User model for authenticated users.

    All registered users have a role (USER or ADMIN).
    Guest users are not stored in the database.
    """

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    first_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    last_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        default=UserRole.USER,
        nullable=False
    )

    # Relationships
    posts: Mapped[List["Post"]] = relationship(
        "Post",
        back_populates="author"
    )
    comments: Mapped[List["Comments"]] = relationship(
        "Comments",
        back_populates="author"
    )
    likes: Mapped[List["Likes"]] = relationship(
        "Likes",
        back_populates="user"
    )
    tokens: Mapped[List["Token"]] = relationship(
        "Token",
        back_populates="user"
    )

    # Follow relationships
    followers: Mapped[List["Follow"]] = relationship(
        "Follow",
        foreign_keys="Follow.followee_uuid",
        back_populates="followee"
    )
    following: Mapped[List["Follow"]] = relationship(
        "Follow",
        foreign_keys="Follow.follower_uuid",
        back_populates="follower"
    )

    def __repr__(self) -> str:
        """Return string representation of the model."""
        return f"<{self.__class__.__name__}(email={self.email},username={self.username},role={self.role})>"
