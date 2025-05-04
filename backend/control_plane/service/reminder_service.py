from uuid import UUID

from numpy.random.mtrand import Sequence

from backend.control_plane.db.models import ReminderStatus
from backend.control_plane.db.repositories.reminder import ReminderRepository
from backend.control_plane.schemas import ReminderSchema
from backend.control_plane.schemas.requests.reminder import ReminderToEditRequestSchema, \
    ReminderMarkAsCompleteRequestSchema, ReminderToEditTimeRequestSchema, ReminderAddSchemaRequest


class RemindersService:
    def __init__(self):
        self.repo = ReminderRepository()

    async def reminder_get(self, reminder_id: UUID):
        return await self.repo.get_by_model_id(model_id=reminder_id)

    async def reminder_update(self, reminder: ReminderToEditRequestSchema) -> ReminderSchema:
        request = reminder.model_dump(exclude_unset=True, exclude_none=True)
        return await self.repo.reminder_update(request=request)

    async def reminder_remove(self, user_id: UUID, reminder_id: UUID) -> bool:
        return await self.repo.delete_model(user_id=user_id, model_id=reminder_id)

    async def reminder_create(self, user_id: UUID, reminder: ReminderAddSchemaRequest) -> ReminderSchema:
        request = reminder.model_dump(exclude_unset=True, exclude_none=True)
        return await self.repo.reminder_create(user_id=user_id, reminder=request)

    async def reminders_get_active(self, user_id: UUID) -> Sequence[ReminderSchema]:
        response = await self.repo.get_models(user_id=user_id, status=ReminderStatus.ACTIVE, removed=False)
        return [ReminderSchema.model_validate(reminder_response) for reminder_response in response]

    async def mark_as_complete(self, reminder: ReminderMarkAsCompleteRequestSchema) -> ReminderSchema:
        reminder = reminder.model_dump(exclude_unset=True, exclude_none=True)  # delete None fields
        response = await self.repo.update_model(model_id=reminder["id"], **reminder)
        return ReminderSchema.model_validate(response)

    async def postpone(self, reminder: ReminderToEditTimeRequestSchema) -> ReminderSchema:
        reminder = reminder.model_dump(exclude_unset=True, exclude_none=True)  # delete None fields
        response = await self.repo.update_model(model_id=reminder["id"], **reminder)
        return ReminderSchema.model_validate(response)


_reminders_service = RemindersService()


def get_reminder_service():
    return _reminders_service
