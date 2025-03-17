from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, func
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID
from ..models.statistics import UserStatistics, DailyActivity
from .base import BaseRepository


class UserStatisticsRepository(BaseRepository[UserStatistics]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserStatistics)

    async def get_by_user(self, user_id: UUID) -> Optional[UserStatistics]:
        """Получение статистики пользователя"""
        stmt = select(UserStatistics).where(UserStatistics.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def ensure_statistics(self, user_id: UUID) -> UserStatistics:
        """
        Гарантирует создание статистики для пользователя,
        если она еще не существует
        """
        stats = await self.get_by_user(user_id)
        if not stats:
            stats = await self.create(
                user_id=user_id,
                reminders_completed=0,
                reminders_forgotten=0
            )
        return stats

    async def increment_completed(self, user_id: UUID, count: int = 1) -> Optional[UserStatistics]:
        """Увеличение счетчика выполненных напоминаний"""
        stats = await self.ensure_statistics(user_id)

        return await self.update(
            stats.user_id,
            reminders_completed=stats.reminders_completed + count,
            last_calculated_at=func.now()
        )

    async def increment_forgotten(self, user_id: UUID, count: int = 1) -> Optional[UserStatistics]:
        """Увеличение счетчика забытых напоминаний"""
        stats = await self.ensure_statistics(user_id)

        return await self.update(
            stats.user_id,
            reminders_forgotten=stats.reminders_forgotten + count,
            last_calculated_at=func.now()
        )

    async def get_user_stats(self, user_id: UUID, period: str = "month") -> Dict[str, Any]:
        """
        Получение полной статистики пользователя за период
        period: 'week', 'month', 'year', 'all'
        """
        stats = await self.ensure_statistics(user_id)

        # Определяем даты периода
        today = date.today()
        if period == "week":
            start_date = today - timedelta(days=today.weekday() + 7)
            end_date = start_date + timedelta(days=6)
        elif period == "month":
            start_date = date(today.year, today.month, 1)
            # Последний день текущего месяца
            if today.month == 12:
                end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)
        elif period == "year":
            start_date = date(today.year, 1, 1)
            end_date = date(today.year, 12, 31)
        else:  # 'all'
            # Получаем самую раннюю активность
            stmt = select(func.min(DailyActivity.date)).where(DailyActivity.user_id == user_id)
            result = await self.session.execute(stmt)
            min_date = result.scalar_one_or_none()

            start_date = min_date if min_date else today
            end_date = today

        # Получаем ежедневную активность
        daily_activity_repo = DailyActivityRepository(self.session)
        daily_activities = await daily_activity_repo.get_activity_range(user_id, start_date, end_date)

        # Формируем результат
        return {
            "user_id": str(user_id),
            "reminders_completed": stats.reminders_completed,
            "reminders_forgotten": stats.reminders_forgotten,
            "period": period,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "daily_activities": [
                {
                    "date": da.date.isoformat(),
                    "completed_items": da.completed_items
                }
                for da in daily_activities
            ]
        }


class DailyActivityRepository(BaseRepository[DailyActivity]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, DailyActivity)

    async def get_by_user_and_date(self, user_id: UUID, target_date: date) -> Optional[DailyActivity]:
        """Получение активности пользователя за день"""
        stmt = select(DailyActivity).where(
            and_(
                DailyActivity.user_id == user_id,
                DailyActivity.date == target_date
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def ensure_activity(self, user_id: UUID, target_date: date) -> DailyActivity:
        """
        Гарантирует создание записи активности для пользователя на дату,
        если она еще не существует
        """
        activity = await self.get_by_user_and_date(user_id, target_date)
        if not activity:
            activity = await self.create(
                user_id=user_id,
                date=target_date,
                completed_items=0
            )
        return activity

    async def increment_completed(self, user_id: UUID, target_date: date, count: int = 1) -> Optional[DailyActivity]:
        """Увеличение счетчика выполненных элементов за день"""
        activity = await self.ensure_activity(user_id, target_date)

        return await self.update(
            activity.id,
            completed_items=activity.completed_items + count
        )

    async def get_activity_range(self, user_id: UUID, start_date: date, end_date: date) -> List[DailyActivity]:
        """Получение активности пользователя за период"""
        stmt = select(DailyActivity).where(
            and_(
                DailyActivity.user_id == user_id,
                DailyActivity.date >= start_date,
                DailyActivity.date <= end_date
            )
        ).order_by(DailyActivity.date)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_streak(self, user_id: UUID) -> int:
        """Расчет текущей серии ежедневной активности пользователя"""
        today = date.today()

        # Получаем все записи активности пользователя, отсортированные по дате (от новых к старым)
        stmt = select(DailyActivity).where(
            DailyActivity.user_id == user_id
        ).order_by(DailyActivity.date.desc())

        result = await self.session.execute(stmt)
        activities = result.scalars().all()

        # Если нет активности, серия = 0
        if not activities:
            return 0

        # Проверяем, есть ли активность сегодня
        if not activities[0].date == today:
            return 0

        # Считаем количество последовательных дней
        streak = 1
        previous_date = today

        for activity in activities[1:]:
            # Если разница в датах 1 день, увеличиваем серию
            if (previous_date - activity.date).days == 1:
                streak += 1
                previous_date = activity.date
            else:
                break

        return streak
