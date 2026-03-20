from sqlalchemy import select, update, delete
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from src.dataBase.core.models import Dialog

from .schemas import DialogCreate


async def get_dialogs(
    session: AsyncSession,
    user_id: int
) -> list[Dialog]:
    stmt = select(Dialog).where(Dialog.user_id == user_id).order_by(Dialog.id.desc())
    result: Result = await session.execute(stmt)
    dialogs = result.scalars().all()
    return list(dialogs)


async def get_dialog(
    session: AsyncSession,
    dialog_id: int,
    user_id: int
) -> Dialog | None:
    stmt = select(Dialog).where(
        Dialog.id == dialog_id,
        Dialog.user_id == user_id
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_dialog(
    session: AsyncSession, 
    dialog_in: DialogCreate, 
    user_id: int
) -> Dialog:
    data = dialog_in.model_dump(exclude={"user_id"})
    dialog = Dialog(**data, user_id=user_id)
    session.add(dialog)
    await session.commit()
    await session.refresh(dialog)
    return dialog

async def update_dialog(
    sesion: AsyncSession,
    dialog_id: int,
    user_prompt: str,
    model_answer: str,
    emotions: str
) -> Dialog:
    result = await sesion.execute(
        select(Dialog).where(Dialog.id == dialog_id)
    )
    dialog = result.scalar_one_or_none()
    
    if dialog:
        dialog.user_prompt += f"\n{user_prompt}"
        dialog.model_answer += f"\n{model_answer}"
        dialog.emotions += f"\n{emotions}"
        
        await sesion.commit()
        await sesion.refresh(dialog)
    return dialog
        
async def delete_dialog(session: AsyncSession, dialog_id: int, user_id: int):
    stmt = delete(Dialog).where(Dialog.id == dialog_id, Dialog.user_id == user_id)
    await session.execute(stmt)
    await session.commit()

async def rename_dialog(session: AsyncSession, dialog_id: int, new_title: str, user_id: int):
    stmt = (
        update(Dialog)
        .where(Dialog.id == dialog_id, Dialog.user_id == user_id)
        .values(title=new_title)
    )
    await session.execute(stmt)
    await session.commit()