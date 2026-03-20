from sqlalchemy import select
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from src.dataBase.core.models import User

from .schemas import CreateUser
from api_v1.auth import utils as pswd_utils

async def get_users(session: AsyncSession) -> list[User]:
    stmt = select(User).order_by(User.id)
    result: Result = await session.execute(stmt)
    users = result.scalars().all()
    return list(users)


async def get_user(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)

async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def create_user(session: AsyncSession, user_in: CreateUser) -> User:
    data = user_in.model_dump()
    password = data.pop("password") 
    hashed_password = pswd_utils.hash_password(password)
    data["hashed_password"] = hashed_password
    user = User(**data)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def update_user(
    session: AsyncSession, 
    user: User, 
    update_data: dict
) -> User:
    for key, value in update_data.items():
        setattr(user, key, value)
    
    await session.commit()
    await session.refresh(user)
    return user
