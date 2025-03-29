from datetime import datetime
from typing import List, Any, Coroutine
from uuid import UUID

from fastapi.params import Depends
import jwt
from mypyc.ir.ops import Sequence
from numpy.random.mtrand import Sequence

from backend.control_plane.config import get_settings
from backend.control_plane.db.models import Reminder
from backend.control_plane.db.repositories.reminder import ReminderRepository
from backend.control_plane.schemas.reminder import ReminderSchema, ReminderSchemaToEdit, ReminderSchemaToEditTime, \
    ReminderMarkAsCompleteSchema, ReminderToDeleteSchema


class RemindersService:
    def __init__(self):
        self.repo = ReminderRepository()

    async def get_reminders(self) -> Sequence[Reminder]:
        return await self.repo.get_active_reminders()

    async def reminder_update(self, reminder: ReminderSchemaToEdit) -> Reminder:
        return await self.repo.update_model(model_id=reminder.id, **vars(reminder))

    async def reminder_delete(self, reminder: ReminderToDeleteSchema) -> bool:
        return await self.repo.delete_model(model_id=reminder.id)

    async def reminder_create(self, request: ReminderSchema) -> Reminder:
        return await self.repo.create(**vars(request))

    async def reminder_get_all(self) -> Sequence[Reminder]:
        return await self.repo.get_models()

    async def mark_as_complete(self, reminder: ReminderMarkAsCompleteSchema) -> Reminder:
        return await self.repo.mark_as_completed(reminder=reminder)

    async def postpone(self, reminder: ReminderSchemaToEditTime) -> Reminder:
        return await self.repo.postpone(reminder=reminder)


_reminders_service = RemindersService()


def get_reminder_service():
    return _reminders_service
