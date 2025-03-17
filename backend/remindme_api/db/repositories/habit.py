from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, func
from datetime import date, timedelta
from typing import List, Optional, Dict
from uuid import UUID
from ..models.habit import Habit, HabitProgress, HabitPeriod
from .base import BaseRepository


class HabitRepository(BaseRepository[Habit]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Habit)

    async def get_active_by_user(self, user_id: UUID) -> List[Habit]:
        """Получение активных привычек пользователя"""
        stmt = select(Habit).where(
            and_(
                Habit.user_id == user_id,
                Habit.removed == False
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_current_by_user(self, user_id: UUID) -> List[Habit]:
        """Получение текущих привычек пользователя (активные и не истекшие)"""
        today = date.today()
        stmt = select(Habit).where(
            and_(
                Habit.user_id == user_id,
                Habit.removed == False,
                or_(
                    Habit.end_date == None,
                    Habit.end_date >= today
                )
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_progress(self, habit_id: UUID, progress: int) -> Optional[Habit]:
        """Обновление прогресса привычки"""
        return await self.update(habit_id, progress=progress)

    async def update_streaks(self, habit_id: UUID, current_streak: int, best_streak: Optional[int] = None) -> Optional[
        Habit]:
        """Обновление текущей и лучшей серии привычки"""
        updates = {"current_streak": current_streak}
        if best_streak is not None:
            updates["best_streak"] = best_streak
        return await self.update(habit_id, **updates)

    async def soft_delete(self, habit_id: UUID) -> Optional[Habit]:
        """Мягкое удаление привычки"""
        return await self.update(habit_id, removed=True)

    async def restore(self, habit_id: UUID) -> Optional[Habit]:
        """Восстановление удаленной привычки"""
        return await self.update(habit_id, removed=False)

    async def get_removed_by_user(self, user_id: UUID) -> List[Habit]:
        """Получение удаленных привычек пользователя"""
        stmt = select(Habit).where(
            and_(
                Habit.user_id == user_id,
                Habit.removed == True
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def calculate_period_dates(self, habit: Habit, target_date: date) -> Dict[str, date]:
        """Расчет начала и конца периода для привычки"""
        if habit.period == HabitPeriod.DAILY:
            return {
                "start": target_date,
                "end": target_date
            }
        elif habit.period == HabitPeriod.WEEKLY:
            # Начало недели (понедельник)
            start = target_date - timedelta(days=target_date.weekday())
            # Конец недели (воскресенье)
            end = start + timedelta(days=6)
            return {"start": start, "end": end}
        elif habit.period == HabitPeriod.MONTHLY:
            # Первый день месяца
            start = date(target_date.year, target_date.month, 1)
            # Последний день месяца
            if target_date.month == 12:
                end = date(target_date.year + 1, 1, 1) - timedelta(days=1)
            else:
                end = date(target_date.year, target_date.month + 1, 1) - timedelta(days=1)
            return {"start": start, "end": end}
        else:  # CUSTOM или другие
            # Для кастомного периода нужна специфическая логика
            # Здесь можно реализовать парсинг custom_period
            return {"start": target_date, "end": target_date}


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
            return await self.update(progress.id, completed=completed)
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

        if habit.period == HabitPeriod.DAILY:
            # Для ежедневных привычек проверяем каждый день
            current_date = until_date
            while current_date >= habit.start_date:
                if current_date in completed_dates:
                    streak += 1
                    current_date -= timedelta(days=1)
                else:
                    break

        elif habit.period == HabitPeriod.WEEKLY:
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

        elif habit.period == HabitPeriod.MONTHLY:
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
        stmt = select(func.count()).select_from(HabitProgress).where(
            and_(
                HabitProgress.habit_id == habit_id,
                HabitProgress.date >= start_date,
                HabitProgress.date <= end_date,
                HabitProgress.completed == True
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()
