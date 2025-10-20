import enum

from sqlalchemy import Column, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class UserRole(enum.Enum):
    ADMIN = "ADMIN"
    USER = "USER"
    GUEST = "GUEST"


class Users(BaseModel):

    __tablename__ = "users"

    username = Column(String(50), unique=True, index=True, nullable=False)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.GUEST)

    # Relationships
    posts = relationship("Post", back_populates="author")
    comments = relationship("Comments", back_populates="author")
    likes = relationship("Likes", back_populates="user")
    tokens = relationship("Token", back_populates="user")

    # Follow relationships
    followers = relationship(
        "Follows",
        foreign_keys="Follows.followee_uuid",
        back_populates="followee"
    )
    following = relationship(
        "Follows",
        foreign_keys="Follows.follower_uuid",
        back_populates="follower"
    )

    def __repr__(self) -> str:
        """Return string representation of the model."""
        return f"<{self.__class__.__name__}(email={self.email},username={self.username},role={self.role})>"
