from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class User(Base):

    username: Mapped[str] 
    hashed_password: Mapped[str] = mapped_column() 
    email: Mapped[str] = mapped_column()
    is_active: Mapped[bool] = mapped_column(default=True)
