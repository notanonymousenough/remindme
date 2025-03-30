from typing import Sequence
from uuid import UUID

from ..models.reminder import Reminder, ReminderStatus
from .base import BaseRepository
from ...schemas import ReminderSchema
from ...schemas.requests.reminder import ReminderMarkAsCompleteRequestSchema, ReminderToEditTimeRequestSchema


class ReminderRepository(BaseRepository[Reminder]):
    def __init__(self):
        super().__init__(Reminder)

    async def get_active_reminders(self, user_id: UUID) -> Sequence[ReminderSchema]:
        response = await self.get_models(user_id=user_id, status=ReminderStatus.ACTIVE, removed=False)
        return [ReminderSchema.model_validate(reminder_response) for reminder_response in response]

    async def mark_as_completed(self, user_id: UUID, reminder: ReminderMarkAsCompleteRequestSchema) -> ReminderSchema:
        reminder = reminder.model_dump(exclude_none=True)
        response = await self.update_model(user_id=user_id, model_id=reminder.id, **vars(reminder))
        return ReminderSchema.model_validate(response)

    async def postpone(self, user_id: UUID, reminder: ReminderToEditTimeRequestSchema) -> ReminderSchema:
        response = await self.update_model(user_id=user_id, model_id=reminder.id, **vars(reminder))
        return ReminderSchema.model_validate(response)
