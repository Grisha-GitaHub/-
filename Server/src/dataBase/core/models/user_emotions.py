from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey
from datetime import datetime
from .base import Base


class UserEmotion(Base):

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    username: Mapped[str] = mapped_column(ForeignKey("users.username"))
    emotions: Mapped[str] = mapped_column(ForeignKey("dialogs.emotions"))
    created_at: Mapped[str] = mapped_column(default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    
