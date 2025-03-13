from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_, func
from datetime import datetime, date
from typing import List, Optional
from uuid import UUID
from ..models.reminder import Reminder, ReminderStatus
from ..models.tag import Tag
from .base import BaseRepository


class ReminderRepository(BaseRepository[Reminder]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Reminder)

    async def get_active_by_user(self, user_id: UUID) -> List[Reminder]:
        """Получение активных напоминаний пользователя"""
        stmt = select(Reminder).where(
            and_(
                Reminder.user_id == user_id,
                Reminder.status == ReminderStatus.ACTIVE,
                Reminder.removed == False
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_tag(self, user_id: UUID, tag_id: UUID) -> List[Reminder]:
        """Получение напоминаний пользователя по тегу"""
        stmt = select(Reminder).join(Reminder.tags).where(
            and_(
                Reminder.user_id == user_id,
                Reminder.removed == False,
                Tag.id == tag_id
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_date(self, user_id: UUID, target_date: date) -> List[Reminder]:
        """Получение напоминаний пользователя на указанную дату"""
        stmt = select(Reminder).where(
            and_(
                Reminder.user_id == user_id,
                Reminder.removed == False,
                func.date(Reminder.time) == target_date
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_status(self, user_id: UUID, status: ReminderStatus) -> List[Reminder]:
        """Получение напоминаний пользователя по статусу"""
        stmt = select(Reminder).where(
            and_(
                Reminder.user_id == user_id,
                Reminder.status == status,
                Reminder.removed == False
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def mark_as_completed(self, reminder_id: UUID, completed_at: Optional[datetime] = None) -> Optional[Reminder]:
        """Отметка напоминания как выполненного"""
        if not completed_at:
            completed_at = datetime.now()
        return await self.update(
            reminder_id,
            status=ReminderStatus.COMPLETED,
            completed_at=completed_at
        )

    async def mark_as_forgotten(self, reminder_id: UUID) -> Optional[Reminder]:
        """Отметка напоминания как забытого"""
        return await self.update(
            reminder_id,
            status=ReminderStatus.FORGOTTEN
        )

    async def postpone(self, reminder_id: UUID, new_time: datetime) -> Optional[Reminder]:
        """Перенос напоминания на другое время"""
        return await self.update(
            reminder_id,
            time=new_time
        )

    async def soft_delete(self, reminder_id: UUID) -> Optional[Reminder]:
        """Мягкое удаление напоминания"""
        return await self.update(
            reminder_id,
            removed=True
        )

    async def restore(self, reminder_id: UUID) -> Optional[Reminder]:
        """Восстановление удаленного напоминания"""
        return await self.update(
            reminder_id,
            removed=False
        )

    async def get_removed_by_user(self, user_id: UUID) -> List[Reminder]:
        """Получение удаленных напоминаний пользователя"""
        stmt = select(Reminder).where(
            and_(
                Reminder.user_id == user_id,
                Reminder.removed == True
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
