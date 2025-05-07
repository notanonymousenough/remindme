from uuid import UUID

from fastapi import HTTPException

from .base import BaseRepository
from .tag import get_tag_repo
from ..engine import get_async_session
from ..models.reminder import Reminder
from ...schemas import ReminderSchema


class ReminderRepository(BaseRepository[Reminder]):
    def __init__(self):
        super().__init__(Reminder)

    async def reminder_update(self,
                              request: dict) -> ReminderSchema:
        reminder_id = request.pop("id")

        async with await get_async_session() as session:
            response = await self.update_model(model_id=reminder_id, session=session, **request)
            if not response:
                raise HTTPException(404, "Wrong entity for reminder_update")

            await session.refresh(response)

        return ReminderSchema.model_validate(response)

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
