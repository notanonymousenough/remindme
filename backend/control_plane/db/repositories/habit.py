from typing import Sequence
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from .base import BaseRepository
from ..engine import get_async_session
from ..models.habit import Habit, HabitProgress
from ...schemas.habit import HabitSchemaResponse
from ...schemas.requests.habit import HabitProgressSchemaPostRequest


class HabitRepository(BaseRepository[Habit]):
    def __init__(self):
        super().__init__(Habit)

    async def find_habits_by_user_id(self, user_id: UUID) -> Sequence[HabitSchemaResponse]:
        async with await get_async_session() as session:
            stmt = select(self.model).where(
                and_(
                    getattr(self.model, "user_id") == user_id
                )
            ).options(selectinload(self.model.progress_records))  # Добавляем eager load
            result = await session.execute(stmt)
            response = result.scalars().all()
        return [HabitSchemaResponse.model_validate(obj) for obj in response]

    async def create_habit(self, user_id: UUID, request: dict) -> HabitSchemaResponse:
        async with await get_async_session() as session:
            obj = self.model(**request)
            obj.user_id = user_id
            session.add(obj)
            await session.flush()
            await session.commit()
            await session.refresh(obj, attribute_names=['progress_records'])
            response = obj
        return HabitSchemaResponse.model_validate(response)

    # habit_progress table
    @staticmethod
    async def add_habit_progress(request: dict) -> HabitProgressSchemaPostRequest:
        async with await get_async_session() as session:
            obj = HabitProgress(**request)
            session.add(obj)

            await session.flush()
            await session.commit()
            return HabitProgressSchemaPostRequest.model_validate(obj)

    @staticmethod
    async def habit_progress_delete_last_record(habit_id: UUID) -> bool:
        async with await get_async_session() as session:
            last_record = await session.scalar(
                select(HabitProgress)
                .where(HabitProgress.habit_id == habit_id)
                .order_by(HabitProgress.record_date.desc())
                .limit(1)
            )
            if last_record:
                await session.delete(last_record)
                await session.flush()
                await session.commit()
                return True
            else:
                return False
