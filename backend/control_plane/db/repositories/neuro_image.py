from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_
from typing import List, Optional
from uuid import UUID
from ..models.neuro_image import NeuroImage, ImageStatus
from .base import BaseRepository


class NeuroImageRepository(BaseRepository[NeuroImage]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, NeuroImage)

    async def get_by_user(self, user_id: UUID, limit: int = 10, offset: int = 0) -> List[NeuroImage]:
        """Получение изображений пользователя с пагинацией"""
        stmt = select(NeuroImage).where(NeuroImage.user_id == user_id).order_by(
            NeuroImage.created_at.desc()
        ).limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_habit(self, habit_id: UUID) -> List[NeuroImage]:
        """Получение изображений для привычки"""
        stmt = select(NeuroImage).where(NeuroImage.habit_id == habit_id).order_by(
            NeuroImage.created_at.desc()
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_reminder(self, reminder_id: UUID) -> List[NeuroImage]:
        """Получение изображений для напоминания"""
        stmt = select(NeuroImage).where(NeuroImage.reminder_id == reminder_id).order_by(
            NeuroImage.created_at.desc()
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_filtered(self, user_id: UUID, habit_id: Optional[UUID] = None,
                           reminder_id: Optional[UUID] = None, limit: int = 10, offset: int = 0) -> List[NeuroImage]:
        """Получение изображений с фильтрацией"""
        conditions = [NeuroImage.user_id == user_id]

        if habit_id:
            conditions.append(NeuroImage.habit_id == habit_id)

        if reminder_id:
            conditions.append(NeuroImage.reminder_id == reminder_id)

        stmt = select(NeuroImage).where(and_(*conditions)).order_by(
            NeuroImage.created_at.desc()
        ).limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        return result.scalars().all()
