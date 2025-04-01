from uuid import UUID

from numpy.random.mtrand import Sequence

from backend.control_plane.db.repositories.reminder import ReminderRepository
from backend.control_plane.schemas import ReminderSchema
from backend.control_plane.schemas.requests.reminder import ReminderToDeleteRequestSchema, ReminderToEditRequestSchema, \
    ReminderMarkAsCompleteRequestSchema, ReminderToEditTimeRequestSchema, ReminderAddSchemaRequest


class RemindersService:
    def __init__(self):
        self.repo = ReminderRepository()

    async def reminder_update(self, user_id: UUID, reminder: ReminderToEditRequestSchema) -> ReminderSchema:
        return await self.repo.reminder_update(user_id=user_id, reminder=reminder)

    async def reminder_delete(self, user_id: UUID, reminder: ReminderToDeleteRequestSchema) -> bool:
        return await self.repo.reminder_delete(user_id=user_id, reminder=reminder)

    async def reminder_create(self, user_id: UUID, request: ReminderAddSchemaRequest) -> ReminderSchema:
        return await self.repo.reminder_create(user_id, request)

    async def reminders_get_active(self, user_id: UUID) -> Sequence[ReminderSchema]:
        return await self.repo.get_active_reminders(user_id=user_id)

    async def mark_as_complete(self, user_id: UUID, reminder: ReminderMarkAsCompleteRequestSchema) -> ReminderSchema:
        return await self.repo.mark_as_completed(user_id=user_id, reminder=reminder)

    async def postpone(self, user_id: UUID, reminder: ReminderToEditTimeRequestSchema) -> ReminderSchema:
        return await self.repo.postpone(user_id=user_id, reminder=reminder)


_reminders_service = RemindersService()


def get_reminder_service():
    return _reminders_service
