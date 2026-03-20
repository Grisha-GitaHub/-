from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, Enum
from datetime import datetime
from .base import Base
import enum

class Feedback(enum.Enum):
    Super = "5"
    Good = "4"
    Normal = "3"
    Bad = "2"
    VeryBad = "1"



class Feedback(Base):

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user_prompt: Mapped[str] = mapped_column(ForeignKey("dialogs.user_prompt"))
    model_answer: Mapped[str] = mapped_column(ForeignKey("dialogs.model_answer"))
    emotions: Mapped[str] = mapped_column(ForeignKey("dialogs.emotions"))
    user_feedback: Mapped[Feedback] = mapped_column(Enum(Feedback), nullable=True)
    user_comment: Mapped[str]
    created_at: Mapped[str] = mapped_column(default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))