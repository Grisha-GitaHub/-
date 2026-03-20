from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.dataBase.core.models import db_helper
from . import crud
from .schemas import Dialog, DialogCreate
from api_v1.auth.jwt_auth import get_current_user

router = APIRouter(tags=["Dialogs"])


@router.get("/", response_model=list[Dialog])
async def get_dialogs(
    session: AsyncSession = Depends(db_helper.session_dependency),
    current_user: int = Depends(get_current_user)
):
    return await crud.get_dialogs(session=session, user_id=current_user.id)


@router.post("/", response_model=Dialog)
async def create_dialog(
    dialog_in: DialogCreate, 
    session: AsyncSession = Depends(db_helper.session_dependency),
    current_user = Depends(get_current_user) 
):
    return await crud.create_dialog(session=session, dialog_in=dialog_in, user_id=current_user.id)


@router.get("/{dialog_id}", response_model=Dialog)
async def get_dialog(
    dialog_id: int,
    session: AsyncSession = Depends(db_helper.session_dependency),
    current_user = Depends(get_current_user)
): 
    
    product = await crud.get_dialog(
        session=session,
        dialog_id=dialog_id,
        user_id=current_user.id
    )
    
    if product is not None:
        return product
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Диалог {dialog_id} не найден"
    )

@router.delete("/{dialog_id}")
async def delete_chat(
    dialog_id: int, 
    current_user = Depends(get_current_user), 
    session: AsyncSession = Depends(db_helper.session_dependency)
):
    await crud.delete_dialog(session, dialog_id, current_user.id)
    return {"status": "deleted"}

@router.patch("/{dialog_id}/rename")
async def rename_chat(
    dialog_id: int, 
    title: str,  # Параметр придет из URL (?title=...)
    current_user = Depends(get_current_user), 
    session: AsyncSession = Depends(db_helper.session_dependency)
):
    print(f"Принятый заголовок: {title}")
    await crud.rename_dialog(session, dialog_id, title, current_user.id)
    return {"status": "renamed"}