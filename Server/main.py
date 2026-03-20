"""
На 18.03
Исправлен 1. Исправить баг появления пустого чата(думаю проблема в том что с экрана general вызывается метод создания чата. 
С экрана Chat тоже вызывается для создания чата и из-за этого происходит создания пустого чата)

2. Сам тест есть, нет првоерки ответов. Реализовать тесты

3. Подогнать дизайн(как минимум экран geneal требуется в доработке)


"""
import asyncio
import redis.asyncio
import random
from concurrent.futures import ProcessPoolExecutor
from fastapi import FastAPI, Query, Request, Depends
import uvicorn
import os
from contextlib import asynccontextmanager
from fastapi.responses import StreamingResponse

from src.dataBase.core.config import settings
from src.dataBase.core.models import Base, User, db_helper
from api_v1 import router as router_v1
from word_processing import WordProcessing
from api_v1.dialogs import crud
from api_v1.dialogs.schemas import DialogCreate
from sqlalchemy.ext.asyncio import AsyncSession
from api_v1.auth import jwt_auth 

@asynccontextmanager
async def lifespan(app: FastAPI):
    global executor
    executor = ProcessPoolExecutor(max_workers=2)
    async with db_helper.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

    await db_helper.engine.dispose()

redis_client = redis.from_url("redis://127.0.0.1:6379", decode_responses=True)

app = FastAPI(lifespan=lifespan)
app.include_router(router=router_v1, prefix=settings.api_v1_prefix)



def ai_logic(message: str):
    raw_answer = WordProcessing(message)
    answer = raw_answer.answer()

    return answer, raw_answer.emotions_str

@app.get("/")
async def message():
    return{"Message": "Success"}

@app.post("/model")
async def handle_message(
    request: Request,
    dialog_id: int = Query(None),
    current_user: User = Depends(jwt_auth.get_current_user),
    session: AsyncSession = Depends(db_helper.session_dependency)
):
    user_id = current_user.id
    data = await request.body()
    message = data.decode("utf-8")
    
    wp = WordProcessing(message)
    
    async def event_generator():
        full_response = []
        for token in wp.answer():
            full_response.append(token)
            yield token
            await asyncio.sleep(0)
        
        final_text = "".join(full_response)
        
        async with db_helper.session_factory() as local_session:
            if dialog_id:
                await crud.update_dialog(
                    sesion=local_session,
                    dialog_id=dialog_id,
                    user_prompt=message,
                    model_answer=final_text,
                    emotions=wp.emotions_str
                )
            else:
                
                dialog_data = DialogCreate(
                    user_prompt=message,
                    model_answer=final_text,
                    emotions=wp.emotions_str,
                    user_id=user_id
                )
                async with db_helper.session_factory() as local_session:
                    await crud.create_dialog(
                        session=local_session, 
                        dialog_in=dialog_data, 
                        user_id=user_id
                    )
    return StreamingResponse(event_generator(), media_type="text/plain")
    # print("Сообщение пришло")

    # print("Начинаю")
    # loop = asyncio.get_running_loop()
    # final_text, emotions = await loop.run_in_executor(executor, ai_logic, message)
    # print("Ответ готов")

    # dialog_data = DialogCreate(
    #     user_prompt=message,
    #     model_answer=final_text,
    #     emotions=emotions,
    #     user_id=user_id
    # )
    # await crud.create_dialog(session=session, dialog_in=dialog_data, user_id=user_id)
    # return {"Doc": final_text}

if __name__ == "__main__":
    

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
