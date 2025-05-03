from typing import Sequence, Annotated
from uuid import UUID

from fastapi import Depends, HTTPException

from .tag import get_tag_repo
from ..engine import get_async_session
from ..models.reminder import Reminder, ReminderStatus
from .base import BaseRepository
from ...schemas import ReminderSchema
from ...schemas.requests.reminder import ReminderMarkAsCompleteRequestSchema, ReminderToEditTimeRequestSchema, \
    ReminderAddSchemaRequest, ReminderToEditRequestSchema
from ...service.tag_service import TagService, get_tag_service


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
                await tag_repo.add_tags_to_reminder(tags=tag_ids, session=session, reminder_id=response.id)

            await session.refresh(response, attribute_names=["_tags"])  # обновление TagSchemas для ReminderSchema

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

            await session.refresh(response, attribute_names=["_tags"])  # обновление TagSchemas для ReminderSchema

        return ReminderSchema.model_validate(response)
