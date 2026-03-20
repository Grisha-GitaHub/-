from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, Enum
import enum
from .base import Base

class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

class Role(Base):

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.GUEST, nullable=False)