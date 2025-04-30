from uuid import UUID

from numpy.random.mtrand import Sequence

from backend.control_plane.db.repositories.reminder import ReminderRepository
from backend.control_plane.schemas import ReminderSchema
from backend.control_plane.schemas.requests.reminder import ReminderToEditRequestSchema, \
    ReminderMarkAsCompleteRequestSchema, ReminderToEditTimeRequestSchema, ReminderAddSchemaRequest
from backend.control_plane.service.tag_service import get_tag_service


class RemindersService:
    def __init__(self):
        self.repo = ReminderRepository()

    async def reminder_update(self, reminder: ReminderToEditRequestSchema) -> ReminderSchema:
        response = reminder.model_dump(exclude_unset=True, exclude_none=True)
        return await self.repo.reminder_update(response=response)

    async def reminder_delete(self, user_id: UUID, reminder_id: UUID) -> bool:
        return await self.repo.reminder_delete(user_id=user_id, reminder_id=reminder_id)

    async def reminder_create(self, user_id: UUID, reminder: ReminderAddSchemaRequest) -> ReminderSchema:
        return await self.repo.reminder_create(user_id=user_id, reminder=reminder, tag_service=get_tag_service())

    async def reminders_get_active(self, user_id: UUID) -> Sequence[ReminderSchema]:
        return await self.repo.get_active_reminders(user_id=user_id)

    async def mark_as_complete(self, reminder: ReminderMarkAsCompleteRequestSchema) -> ReminderSchema:
        return await self.repo.mark_as_completed(reminder=reminder)

    async def postpone(self, reminder: ReminderToEditTimeRequestSchema) -> ReminderSchema:
        return await self.repo.postpone(reminder=reminder)


_reminders_service = RemindersService()


def get_reminder_service():
    return _reminders_service
