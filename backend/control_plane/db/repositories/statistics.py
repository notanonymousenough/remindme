from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, func
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID
from ..models.statistics import UserStatistics
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

        return await self.update_model(
            stats.user_id,
            reminders_completed=stats.reminders_completed + count,
            last_calculated_at=func.now()
        )

    async def increment_forgotten(self, user_id: UUID, count: int = 1) -> Optional[UserStatistics]:
        """Увеличение счетчика забытых напоминаний"""
        stats = await self.ensure_statistics(user_id)

        return await self.update_model(
            stats.user_id,
            reminders_forgotten=stats.reminders_forgotten + count,
            last_calculated_at=func.now()
        )
