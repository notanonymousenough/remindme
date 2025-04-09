from typing import List, Union, Sequence
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepository
from .tag import get_tag_repo
from ..engine import get_async_session
from ..models import ReminderStatus
from ..models.reminder import Reminder
from ...schemas import ReminderSchema
from ...schemas.requests.reminder import ReminderEditStatusRequest, ReminderEditRequest
from ...utils import timeutils


class ReminderRepository(BaseRepository[Reminder]):
    def __init__(self):
        super().__init__(Reminder)

    async def get_removed(self, user_id: UUID, reminder_statuses: List[ReminderStatus], session=None) -> Sequence[ReminderSchema]:
        if session:
            return await self._get_removed(user_id, reminder_statuses, session)
        else:
            async with await get_async_session() as session:
                return await self._get_removed(user_id, reminder_statuses, session)

    async def _get_removed(self, user_id: UUID, reminder_statuses: List[ReminderStatus], session) -> Sequence[ReminderSchema]:
        stmt = select(self.model).where(
            and_(
                getattr(self.model, "user_id") == user_id,
                getattr(self.model, "status") in reminder_statuses
            ))
        response = await session.execute(stmt)
        return response.scalars().all()

    async def reminder_update(self,
                              reminder: Union[ReminderEditRequest, ReminderEditStatusRequest],
                              session: AsyncSession = None) -> ReminderSchema:
        if session:
            return await self._reminder_update(reminder, session)
        else:
            async with await get_async_session() as session:
                return await self._reminder_update(reminder, session)

    async def _reminder_update(self,
                               reminder: Union[ReminderEditRequest, ReminderEditStatusRequest],
                               session: AsyncSession = None):
        request = reminder.model_dump(exclude_unset=True, exclude_none=True)

        reminder_id = request.pop("id")

        async with await get_async_session() as session:
            # TODO убрать нахуй эти функции и сразу base.update_model вызывать везде
            response = await self.update_model(model_id=reminder_id, session=session, **request)
            if not response:
                raise HTTPException(404, "Wrong entity for reminder_update")

            await session.refresh(response)

        return ReminderSchema.model_validate(response)

    async def get_active_reminders(self, user_id: UUID) -> Sequence[ReminderSchema]:
        response = await self.get_models(user_id=user_id, status=ReminderStatus.ACTIVE, removed=False)
        return [ReminderSchema.model_validate(reminder_response) for reminder_response in response]


    async def reminder_create(self,
                              user_id: UUID,
                              reminder: dict) -> ReminderSchema:
        tag_ids = reminder.pop("tags")

        async with await get_async_session() as session:
            response = await self.create(user_id=user_id, session=session, **reminder)

            if not response:
                raise HTTPException(404, "Wrong entity for reminder_create")

            if tag_ids:
                tag_repo = get_tag_repo()
                await tag_repo.add_tags_to_reminder(tag_ids=tag_ids, session=session, reminder_id=response.id)

            await session.refresh(response)

        return ReminderSchema.model_validate(response)

    async def mark_sent(self, reminder_id: UUID, sent=True) -> Reminder:
        return await self.update_model(model_id=reminder_id, notification_sent=sent)

    async def take_for_sending(self, limit: int) -> Sequence[Reminder]:
        async with get_async_session() as session:
            async with session.begin():
                get_stmt = (
                    select(Reminder)
                    .where(
                        and_(
                            Reminder.status == ReminderStatus.ACTIVE,
                            Reminder.notification_sent == False,
                            Reminder.removed == False,
                            Reminder.time <= timeutils.get_utc_now(),
                        )
                    )
                    .limit(limit)
                    .with_for_update(skip_locked=True)
                )
                result = await session.execute(get_stmt)
                reminders = result.scalars().all()

                if not reminders:
                    return []

                reminder_ids = [reminder.id for reminder in reminders]
                update_stmt = (
                    update(Reminder)
                    .where(Reminder.id.in_(reminder_ids))
                    .values(notification_sent=True)
                )
                await session.execute(update_stmt)
                await session.commit()

                return reminders