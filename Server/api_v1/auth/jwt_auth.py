from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import asyncio
import random
from datetime import datetime, timedelta, timezone
import redis.asyncio as redis
from api_v1.users.schemas import UserSchema

from api_v1.auth import utils as auth_utils

from sqlalchemy import select
from sqlalchemy.engine import Result

from sqlalchemy.ext.asyncio import AsyncSession
from src.dataBase.core.models import User
from src.dataBase.core.models.db_helper import db_helper 


from api_v1.users.schemas import CreateUser, LoginUser
from api_v1.users import crud
from src.dataBase.core.config import settings

redis_client = redis.from_url("redis://127.0.0.1:6379", decode_responses=True)

router = APIRouter(tags=["Auth"])

http_bearer = HTTPBearer()

def create_access_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.auth_JWT.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire})
    return auth_utils.encode_jwt(payload)

async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(http_bearer),
    session: AsyncSession = Depends(db_helper.get_scoped_session)
) -> User:
    try:
        payload: str = auth_utils.decoded_jwt(token.credentials)
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен не валиден")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен не валиден")

    user = await crud.get_user(session, user_id=int(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден")
    
    return user


@router.post("/send-code")
async def send_confirmation_code(email: str):
    code = str(random.randint(1000,9999))
    
    await redis_client.set(name=f"confirm:{email}", value=code, ex=300)
    
    return {"message": "Код отправлен", "test_code": code}

@router.post("/verify-and-register")
async def verify_and_register(
    user_in: CreateUser, 
    code: str, 
    session: AsyncSession = Depends(db_helper.get_scoped_session)):
    
    saved_code = await redis_client.get(f"confirm:{user_in.email}")
    if not saved_code:
        raise HTTPException(status_code=400, detail="Код истек или не запрашивался")
    
    if saved_code != code:
        raise HTTPException(status_code=400, detail="Неверный код")
    
    new_user = await crud.create_user(session, user_in)
    await redis_client.delete(f"confirm:{user_in.email}")
    
    token = create_access_token(data={"sub": str(new_user.id)})
    
    
    return {
        "access_token": token,
        "token_type": settings.auth_JWT.TOKEN_TYPE,
        "user": {"id": new_user.id, "username": new_user.username}
    }
    
@router.post("/login")
async def login(
    user_in: LoginUser,
    session: AsyncSession = Depends(db_helper.get_scoped_session)
):
    user = await crud.get_user_by_email(session, user_in.email)
    
    if not user or not auth_utils.validate_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
     
    token = create_access_token(data={"sub": str(user.id), "username": user.username, "email": user.email})
    
    return {
        "access_token": token,
        "token_type": settings.auth_JWT.TOKEN_TYPE,
        "email": user.email
    }

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return{
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email
    }