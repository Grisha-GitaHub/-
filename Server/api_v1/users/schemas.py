from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Annotated
from annotated_types import MinLen, MaxLen

class CreateUser(BaseModel):
    username: Annotated[str, MinLen(3), MaxLen(32)]
    password: str | bytes
    email: EmailStr 

class LoginUser(BaseModel):
    email: EmailStr
    password: str | bytes
    
    
class UserSchema(BaseModel):
    model_config = ConfigDict(strict=True)
    username: Annotated[str, MinLen(3), MaxLen(32)]
    hashed_password: str | bytes
    email: EmailStr 
    active: bool = True