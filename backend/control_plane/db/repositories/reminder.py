from numpy.random.mtrand import Sequence
from datetime import datetime
from typing import Optional

from ..models.reminder import Reminder, ReminderStatus
from .base import BaseRepository
from ...schemas.reminder import ReminderSchemaToEditTime
from ...schemas.requests.reminder import ReminderMarkAsCompleteRequestSchema


class ReminderRepository(BaseRepository[Reminder]):
    def __init__(self):
        super().__init__(Reminder)

    async def get_active_reminders(self) -> Sequence[Reminder]:
        return await self.get_models(status=ReminderStatus.ACTIVE, removed=False)

    async def mark_as_completed(self, reminder: ReminderMarkAsCompleteRequestSchema) -> Reminder:
        reminder = reminder.model_dump(exclude_none=True)  # model_dump() == dict()

        return await self.update_model(**vars(reminder))

    async def postpone(self, reminder: ReminderSchemaToEditTime) -> Reminder:
        return await self.update_model(model_id=reminder.id, time=reminder.time)
