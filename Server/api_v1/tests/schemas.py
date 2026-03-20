from pydantic import BaseModel
from typing import List, Optional, Dict

class QuestionSchema(BaseModel):
    id: int
    # Меняем text на question_text, чтобы совпало с JSON
    question_text: str 
    # Делаем type необязательным (Optional), так как в JSON его нет
    type: Optional[str] = "choice" 
    options: Optional[List[str]] = None
    # Добавляем правильный ответ, раз он есть в файле
    correct_answer: Optional[str] = None
    scores_list: Optional[List[Dict[str, int]]] = [] 
    correct_answer: Optional[str] = None

class TestSchema(BaseModel):
    id: str
    name: str 
    desc: Optional[str] = None
    questions: List[QuestionSchema]
    