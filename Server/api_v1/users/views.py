from fastapi import APIRouter, Depends, HTTPException 
from sqlalchemy.ext.asyncio import AsyncSession
from .schemas import CreateUser
from api_v1.users import crud


from src.dataBase.core.models.db_helper import db_helper 
from api_v1.auth import jwt_auth


router = APIRouter(tags=["Users"])

@router.post("/register")
async def create_user(
    user: CreateUser,
    session: AsyncSession = Depends(db_helper.get_scoped_session)):
    return await crud.create_user(session=session, user_in=user)


@router.patch("/update_me")
async def update_user_profile(
    user_update: dict,  
    session: AsyncSession = Depends(db_helper.get_scoped_session),
    current_user = Depends(jwt_auth.get_current_user),
):
    if "username" not in user_update:
        raise HTTPException(
            status_code=400, 
            detail="Username field is required"
        )
        
    return await crud.update_user(
        session=session, 
        user=current_user, 
        update_data={"username": user_update["username"]}
    )

