from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .models import Task


async def get_tasks(session: AsyncSession):
    result = await session.execute(select(Task))
    return result.scalars().all()


async def create_task(session: AsyncSession, task_data):
    task = Task(**task_data)
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task
