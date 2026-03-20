from pydantic import BaseModel, ConfigDict
from typing import Optional

class DialogBase(BaseModel):
    user_prompt: Optional[str] = ""
    model_answer: Optional[str] = ""
    emotions: Optional[str] = ""


class DialogCreate(DialogBase):
    title: Optional[str] = "Новый диалог"


class Dialog(DialogBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    title: Optional[str] = None
