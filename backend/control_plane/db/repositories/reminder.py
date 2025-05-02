from typing import Sequence, Annotated
from uuid import UUID

from fastapi import Depends, HTTPException

from .tag import get_tag_repo
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
                              request: dict,
                              tag_service: TagService) -> ReminderSchema:
        tags = request.pop("tags")
        reminder_id = request.pop("id")

        response = await self.update_model(model_id=reminder_id, **request)
        if not response:
            raise HTTPException(404, "Wrong entity for reminder_update")

        if tags:
            await tag_service.add_tags_to_reminder(tags=tags, reminder_id=response.id)

        response.tags = tags
        return ReminderSchema.model_validate(response)

    async def reminder_create(self,
                              user_id: UUID,
                              reminder: dict,
                              tag_service: TagService) -> ReminderSchema:
        tags = reminder.pop("tags")

        response = await self.create(user_id=user_id, **reminder)

        if tags:
            await tag_service.add_tags_to_reminder(tags=tags, reminder_id=response.id)

        response.tags = tags

        return ReminderSchema.model_validate(response)
