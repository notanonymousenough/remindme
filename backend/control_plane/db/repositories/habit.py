import datetime
from typing import Sequence
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

    async def get_active_habits(self, user_id: UUID) -> Sequence[Habit]:
        response = await self.get_models(user_id=user_id, removed=False)
        # TODO: [HabitSchema.model_validate(habit) for habit in response]
        return response


class HabitProgressRepository(BaseRepository[HabitProgress]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, HabitProgress)

    async def get_by_habit_and_date(self, habit_id: UUID, target_date: date) -> Optional[HabitProgress]:
        """Получение прогресса привычки на указанную дату"""
        stmt = select(HabitProgress).where(
            and_(
                HabitProgress.habit_id == habit_id,
                HabitProgress.date == target_date
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def mark_completed(self, habit_id: UUID, target_date: date, completed: bool = True) -> HabitProgress:
        """Отметка прогресса привычки на указанную дату"""
        progress = await self.get_by_habit_and_date(habit_id, target_date)

        if progress:
            # Обновляем существующую запись
            return await self.update_model(progress.id, completed=completed)
        else:
            # Создаем новую запись
            return await self.create(
                habit_id=habit_id,
                date=target_date,
                completed=completed
            )

    async def get_progress_for_period(self, habit_id: UUID, start_date: date, end_date: date) -> List[HabitProgress]:
        """Получение прогресса привычки за период"""
        stmt = select(HabitProgress).where(
            and_(
                HabitProgress.habit_id == habit_id,
                HabitProgress.date >= start_date,
                HabitProgress.date <= end_date
            )
        ).order_by(HabitProgress.date)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_streak(self, habit_id: UUID, until_date: date = None) -> int:
        """Расчет текущей серии привычки"""
        if until_date is None:
            until_date = date.today()

        # Получаем все записи до указанной даты, сортированные по дате (от новых к старым)
        stmt = select(HabitProgress).where(
            and_(
                HabitProgress.habit_id == habit_id,
                HabitProgress.date <= until_date
            )
        ).order_by(HabitProgress.date.desc())

        result = await self.session.execute(stmt)
        progress_records = result.scalars().all()

        # Получаем информацию о привычке для определения периодичности
        habit_stmt = select(Habit).where(Habit.id == habit_id)
        habit_result = await self.session.execute(habit_stmt)
        habit = habit_result.scalars().first()

        if not habit or not progress_records:
            return 0

        # Расчет серии в зависимости от периодичности привычки
        streak = 0
        last_date = until_date

        # Получаем все даты с отметками о выполнении
        completed_dates = {p.date for p in progress_records if p.completed}

        if habit.period == HabitInterval.DAILY:
            # Для ежедневных привычек проверяем каждый день
            current_date = until_date
            while current_date >= habit.start_date:
                if current_date in completed_dates:
                    streak += 1
                    current_date -= timedelta(days=1)
                else:
                    break

        elif habit.period == HabitInterval.WEEKLY:
            # Для еженедельных привычек проверяем каждую неделю
            current_week_start = until_date - timedelta(days=until_date.weekday())
            while current_week_start >= habit.start_date:
                week_end = current_week_start + timedelta(days=6)
                # Проверяем, есть ли хотя бы одна отметка за неделю
                if any(d in completed_dates for d in [current_week_start + timedelta(days=i) for i in range(7)]):
                    streak += 1
                    current_week_start -= timedelta(days=7)
                else:
                    break

        elif habit.period == HabitInterval.MONTHLY:
            # Для ежемесячных привычек проверяем каждый месяц
            current_month = until_date.replace(day=1)
            while current_month >= habit.start_date:
                # Определяем последний день месяца
                if current_month.month == 12:
                    month_end = date(current_month.year + 1, 1, 1) - timedelta(days=1)
                else:
                    month_end = date(current_month.year, current_month.month + 1, 1) - timedelta(days=1)

                # Проверяем, есть ли хотя бы одна отметка за месяц
                month_dates = []
                current_day = current_month
                while current_day <= month_end:
                    month_dates.append(current_day)
                    current_day += timedelta(days=1)

                if any(d in completed_dates for d in month_dates):
                    streak += 1
                    # Переходим к предыдущему месяцу
                    if current_month.month == 1:
                        current_month = date(current_month.year - 1, 12, 1)
                    else:
                        current_month = date(current_month.year, current_month.month - 1, 1)
                else:
                    break

        # Для кастомных периодов нужна отдельная логика

        return streak

    async def count_completed_days(self, habit_id: UUID, start_date: date, end_date: date) -> int:
        """Подсчет количества дней с выполненной привычкой за период"""
        stmt = select(func.count_models()).select_from(HabitProgress).where(
            and_(
                HabitProgress.habit_id == habit_id,
                HabitProgress.date >= start_date,
                HabitProgress.date <= end_date,
                HabitProgress.completed == True
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()
