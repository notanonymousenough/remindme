import jwt
from fastapi import Depends
from numpy.random.mtrand import Sequence
from sqlalchemy.future import select
from sqlalchemy import and_, or_, func, insert
from datetime import datetime, date
from typing import List, Optional
from uuid import UUID

from ..engine import get_async_session
from ..models.reminder import Reminder, ReminderStatus
from ..models.tag import Tag
from .base import BaseRepository
from ...config import get_settings


class ReminderRepository(BaseRepository[Reminder]):
    def __init__(self):
        super().__init__(Reminder)

    async def get_active_reminders(self, token: str = Depends(get_settings().OAUTH2_SCHEME)) -> Sequence[Reminder]:
        async with await get_async_session() as session:
            user_id = jwt.decode(token, get_settings().SECRET_KEY, algorithms=[get_settings().ALGORITHM])
            """Получение активных напоминаний пользователя"""
            stmt = select(Reminder).where(
                and_(
                    Reminder.user_id == user_id,
                    Reminder.status == ReminderStatus.ACTIVE,
                    Reminder.removed == False
                ).returning(Reminder)
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    async def mark_as_completed(
            self,
            reminder_id: UUID,
            completed_at: Optional[datetime] = None,
            token: str = Depends(get_settings().OAUTH2_SCHEME)
    ) -> Optional[Reminder]:
        async with await get_async_session() as session:
            user_id = jwt.decode(token, get_settings().SECRET_KEY, algorithms=[get_settings().ALGORITHM])

            if not completed_at:
                completed_at = datetime.now()

            stmt = select(Reminder).where(
                and_(
                    Reminder.user_id == user_id,
                    Reminder.status == ReminderStatus.ACTIVE,
                    Reminder.removed == False
                ).returning(Reminder)
            )

            return await self.update_model(
                reminder_id,
                status=ReminderStatus.COMPLETED,
                completed_at=completed_at
            )

    async def postpone(
            self,
            reminder_id: UUID,
            new_time: datetime,
            token: str = Depends(get_settings().OAUTH2_SCHEME)
    ) -> Optional[Reminder]:
        async with await get_async_session() as session:
            user_id = jwt.decode(token, get_settings().SECRET_KEY, algorithms=[get_settings().ALGORITHM])
            return await self.update_model(
                time=new_time
            )
