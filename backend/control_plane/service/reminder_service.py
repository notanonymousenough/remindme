from uuid import UUID

from numpy.random.mtrand import Sequence

from backend.control_plane.db.repositories.reminder import ReminderRepository
from backend.control_plane.schemas import ReminderSchema
from backend.control_plane.schemas.requests.reminder import ReminderToDeleteRequestSchema, ReminderToEditRequestSchema, \
    ReminderMarkAsCompleteRequestSchema, ReminderToEditTimeRequestSchema


class RemindersService:
    def __init__(self):
        self.repo = ReminderRepository()

    async def get_reminders(self, user_id: UUID) -> Sequence[ReminderSchema]:
        response = await self.repo.get_active_reminders(user_id=user_id)
        return [ReminderSchema.model_validate(reminder_response) for reminder_response in response]

    async def reminder_update(self, user_id: UUID, reminder: ReminderToEditRequestSchema) -> ReminderSchema:
        response = await self.repo.update_model(user_id=user_id, model_id=reminder.id, **vars(reminder.model_dump()))
        # request = utils.get_alchemy_from_pydantic(reminder) TODO(ARSEN)
        # await self.repo.update_model(alchemy_model = request)
        return ReminderSchema.model_validate(response)

    async def reminder_delete(self, user_id: UUID, reminder: ReminderToDeleteRequestSchema) -> bool:
        response = await self.repo.delete_model(user_id=user_id, model_id=reminder.id)
        return response

    async def reminder_create(self, user_id: UUID, request: ReminderSchema) -> ReminderSchema:
        response = await self.repo.create(user_id=user_id, **vars(request))
        return ReminderSchema.model_validate(response)

    async def reminder_get_all_active(self, user_id: UUID) -> Sequence[ReminderSchema]:
        return await self.repo.get_active_reminders(user_id=user_id)

    async def mark_as_complete(self, user_id: UUID, reminder: ReminderMarkAsCompleteRequestSchema) -> ReminderSchema:
        return await self.repo.mark_as_completed(user_id=user_id, reminder=reminder)

    async def postpone(self, user_id: UUID, reminder: ReminderToEditTimeRequestSchema) -> ReminderSchema:
        return await self.repo.postpone(user_id=user_id, reminder=reminder)


_reminders_service = RemindersService()


def get_reminder_service():
    return _reminders_service
