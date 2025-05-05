import datetime
from typing import Sequence, List
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from .base import BaseRepository
from ..engine import get_async_session
from ..models.habit import Habit, HabitProgress
from ...schemas.habit import HabitSchemaResponse
from ...schemas.requests.habit import HabitProgressSchemaPostRequest
from ...utils import timeutils

class HabitRepository(BaseRepository[Habit]):
    def __init__(self):
        super().__init__(Habit)

    async def find_habits_by_user_id(self, user_id: UUID) -> Sequence[HabitSchemaResponse]:
        async with get_async_session() as session:
            stmt = select(self.model).where(
                and_(
                    getattr(self.model, "user_id") == user_id
                )
            ).options(selectinload(self.model.progress_records))  # Добавляем eager load
            result = await session.execute(stmt)
            response = result.scalars().all()
        return [HabitSchemaResponse.model_validate(obj) for obj in response]

    async def create_habit(self, user_id: UUID, request: dict) -> HabitSchemaResponse:
        async with get_async_session() as session:
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
        async with get_async_session() as session:
            obj = HabitProgress(**request)
            session.add(obj)

            await session.flush()
            await session.commit()
            return HabitProgressSchemaPostRequest.model_validate(obj)

    @staticmethod
    async def habit_progress_delete_last_record(habit_id: UUID) -> bool:
        async with get_async_session() as session:
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

    async def take_for_image_generation(self) -> Sequence[Habit]:
        current_time = timeutils.get_utc_now()
        two_weeks_ago = current_time - datetime.timedelta(weeks=2)
        async with get_async_session() as session:
            async with session.begin():
                get_stmt = (
                    select(Habit)
                    .where(
                        and_(
                            Habit.created_at >= two_weeks_ago,
                            Habit.removed == False
                        )
                    )
                )
                result = await session.execute(get_stmt)
                habits = result.scalars().all()

                if not habits:
                    return []
                # TODO: [HabitSchema.model_validate(habit) for habit in habits]
                return habits

    async def get_progress_for_period(self, habit_id: UUID, start_date: datetime.date, end_date: datetime.date) -> List[HabitProgress]:
        """Получение прогресса привычки за период"""
        async with get_async_session() as session:
            stmt = select(HabitProgress).where(
                and_(
                    HabitProgress.habit_id == habit_id,
                    HabitProgress.record_date >= start_date,
                    HabitProgress.record_date <= end_date
                )
            ).order_by(HabitProgress.record_date)

            result = await session.execute(stmt)
            return result.scalars().all()

    async def get_active_habits(self, user_id: UUID) -> Sequence[HabitSchemaResponse]:
        response = await self.get_models(user_id=user_id, removed=False)
        return [HabitSchemaResponse.model_validate(habit) for habit in response]
