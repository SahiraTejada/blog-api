import enum
from sqlalchemy import Column, String, Enum
from app.models.base import BaseModel
from sqlalchemy.orm import relationship


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
    role = Column(Enum(UserRole), default=UserRole.GUEST, nullable=False)

    # Relationships
    posts = relationship("Post", back_populates="author")

    def __repr__(self) -> str:
        """Return string representation of the model."""
        return f"<{self.__class__.__name__}(email={self.email},username={self.username},role={self.role})>"
