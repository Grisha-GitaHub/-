from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

from .base import Base
from .user import User


class Dialog(Base):
    title: Mapped[str] = mapped_column(String(100), nullable=True, default="Новый чат")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user_prompt: Mapped[str]
    model_answer: Mapped[str]
    emotions: Mapped[str]
