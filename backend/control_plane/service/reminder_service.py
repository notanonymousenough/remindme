from datetime import datetime
from typing import List
from uuid import UUID

from fastapi.params import Depends

from backend.control_plane.db.models import Reminder
from backend.control_plane.db.repositories.reminder import ReminderRepository
from backend.control_plane.schemas.reminder import ReminderSchema


class RemindersService:
    def __init__(self):
        self.repo = ReminderRepository()

    # Спросить про аутентификацию, как будет юзер айди передаваться и использовать его в сервисе

    async def get_reminders(self, user_id: UUID) -> List[ReminderSchema]:
        reminder_models = await self.repo.get_active_by_user(user_id)
        result = []
        for reminder_model in reminder_models:
            result.append(ReminderSchema.model_validate(reminder_model))

        return result

    async def reminder_update(self, reminder_id: UUID, **kwargs) -> Reminder:
        # todo: оперируем схемами
        return await self.repo.update(reminder_id, **kwargs)

    async def reminder_delete(self, reminder_id: UUID):
        return await self.repo.delete(reminder_id)

    async def reminder_put(self, request: ReminderSchema):
        return await self.repo.create(**vars(request))

    async def reminder_get_all(self):
        return await self.repo.get_all()

    async def mark_as_complete(self, reminder_id: UUID):
        return await self.repo.mark_as_completed(reminder_id)

    async def postpone(self, reminder_id: UUID, new_time: datetime):
        return await self.repo.postpone(reminder_id=reminder_id, new_time=new_time)


_reminders_service = RemindersService()


def get_reminder_service():
    return _reminders_service
