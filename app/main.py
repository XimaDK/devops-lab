from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from .database import Base, DATABASE_URL
from .models import Task
from .crud import get_tasks, create_task
from typing import Optional
from pydantic import BaseModel, ValidationError

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

app = FastAPI(title="FastAPI Task Service")


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None


async def get_session():
    async with async_session() as session:
        yield session


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/")
async def root():
    return {"message": "FastAPI Task Service is running!"}


@app.get("/tasks")
async def read_tasks(session: AsyncSession = Depends(get_session)):
    return await get_tasks(session)


@app.post("/tasks")
async def create_task_endpoint(task: TaskCreate, session: AsyncSession = Depends(get_session)):
    try:
        return await create_task(session, task.dict())
    except ValidationError as ve:
        # Ошибки валидации Pydantic
        raise HTTPException(status_code=422, detail=ve.errors())
    except Exception as e:
        # Любые другие ошибки → HTTP 400
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/tasks/{task_id}")
async def get_task(task_id: int, session: AsyncSession = Depends(get_session)):
    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int, session: AsyncSession = Depends(get_session)):
    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await session.delete(task)
    await session.commit()
    return {"message": "Task deleted"}
