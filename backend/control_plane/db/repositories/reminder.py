from typing import Sequence, Annotated
from uuid import UUID
from fastapi import HTTPException
from datetime import datetime, UTC
from sqlalchemy import select, update, and_

from ..engine import get_async_session
from ..models.reminder import Reminder, ReminderStatus
from .base import BaseRepository
from .tag import get_tag_repo
from ..engine import get_async_session
from ..models.reminder import Reminder
from ...schemas import ReminderSchema
from ...schemas.requests.reminder import ReminderMarkAsCompleteRequestSchema, ReminderToEditTimeRequestSchema, \
    ReminderAddSchemaRequest, ReminderToEditRequestSchema
from ...service.tag_service import TagService, get_tag_service
from ...utils import timeutils


class ReminderRepository(BaseRepository[Reminder]):
    def __init__(self):
        super().__init__(Reminder)

    async def reminder_update(self,
                              request: dict) -> ReminderSchema:
        tag_ids = request.pop("tags")
        reminder_id = request.pop("id")

        async with await get_async_session() as session:
            response = await self.update_model(model_id=reminder_id, session=session, **request)
            if not response:
                raise HTTPException(404, "Wrong entity for reminder_update")

            if tag_ids:
                tag_repo = get_tag_repo()
                await tag_repo.add_tags_to_reminder(tag_ids=tag_ids, session=session, reminder_id=response.id)

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