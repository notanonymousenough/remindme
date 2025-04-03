from typing import Sequence, Annotated
from uuid import UUID

from fastapi import Depends

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
                              reminder: ReminderToEditRequestSchema,
                              tag_service: TagService) -> ReminderSchema:
        reminder = reminder.model_dump(exclude_unset=True, exclude_none=True)

        tags = reminder.pop("tags")
        if tags:
            await tag_service.add_tags_to_reminder(tags=tags, reminder_id=reminder["id"])

        response = await self.update_model(model_id=reminder["id"], **reminder)
        return ReminderSchema.model_validate(response)

    async def reminder_create(self,
                              user_id: UUID,
                              reminder: ReminderAddSchemaRequest,
                              tag_service: TagService) -> ReminderSchema:
        reminder = reminder.model_dump(exclude_unset=True, exclude_none=True)

        tags = reminder.pop("tags")

        response = await self.create(user_id=user_id, **reminder)

        if tags:
            await tag_service.add_tags_to_reminder(tags=tags, reminder_id=response.id)

        return ReminderSchema.model_validate(response)

    async def reminder_delete(self, user_id: UUID, reminder_id: UUID) -> bool:
        # TODO get_tag from reminder_id and DELETE
        return await self.delete_model(user_id=user_id, model_id=reminder_id)

    async def get_active_reminders(self, user_id: UUID) -> Sequence[ReminderSchema]:
        response = await self.get_models(user_id=user_id, status=ReminderStatus.ACTIVE, removed=False)
        return [ReminderSchema.model_validate(reminder_response) for reminder_response in response]

    async def mark_as_completed(self, reminder: ReminderMarkAsCompleteRequestSchema) -> ReminderSchema:
        reminder = reminder.model_dump(exclude_unset=True, exclude_none=True)  # delete None fields
        response = await self.update_model(model_id=reminder["id"], **reminder)
        return ReminderSchema.model_validate(response)

    async def postpone(self, reminder: ReminderToEditTimeRequestSchema) -> ReminderSchema:
        reminder = reminder.model_dump(exclude_unset=True, exclude_none=True)  # delete None fields
        response = await self.update_model(model_id=reminder["id"], **reminder)
        return ReminderSchema.model_validate(response)
