import datetime
import logging
from typing import Sequence
from uuid import UUID

from backend.control_plane.db.models import ReminderStatus
from backend.control_plane.db.repositories.reminder import ReminderRepository
from backend.control_plane.db.repositories.user import UserRepository
from backend.control_plane.schemas import ReminderSchema
from backend.control_plane.schemas.requests.reminder import ReminderToEditRequestSchema, \
    ReminderMarkAsCompleteRequestSchema, ReminderToEditTimeRequestSchema, ReminderAddSchemaRequest
from backend.control_plane.service.tag_service import get_tag_service
from backend.control_plane.utils import yandex_gpt_client, timeutils

logger = logging.getLogger("reminder_service")

class RemindersService:
    def __init__(self):
        self.repo = ReminderRepository()
        self.user_repo = UserRepository()

    async def reminder_get(self, reminder_id: UUID):
        return await self.repo.get_by_model_id(model_id=reminder_id)

    async def reminder_update(self, reminder: ReminderToEditRequestSchema) -> ReminderSchema:
        request = reminder.model_dump(exclude_unset=True, exclude_none=True)
        return await self.repo.reminder_update(request=request)

    async def reminder_remove(self, user_id: UUID, reminder_id: UUID) -> bool:
        return await self.repo.delete_model(user_id=user_id, model_id=reminder_id)

    async def reminder_create(self, user_id: UUID, reminder: ReminderAddSchemaRequest) -> ReminderSchema:
        # Missing time in request means that we need an AI help without creation in DB
        if reminder.time is None:
            # todo: check global quota (maybe raise exception QuotaExceeded)
            return await self.create_with_ai_predicted_time(user_id=user_id, reminder_text=reminder.text)
        # Otherwise create reminder in DB and return it
        user = await self.user_repo.get_user(user_id)
        reminder.time = timeutils.convert_user_timezone_to_utc(reminder.time, user.timezone_offset)

        request = reminder.model_dump(exclude_unset=True, exclude_none=True)
        return await self.repo.reminder_create(user_id=user_id, reminder=request)

    async def create_with_ai_predicted_time(self, user_id: UUID, reminder_text: str) -> ReminderSchema:
        user = await self.user_repo.get_user(user_id=user_id)
        try:
            reminder_time = await yandex_gpt_client.predict_reminder_time(user.timezone_offset, reminder_text)
            return ReminderSchema(
                user_id=user_id,
                text=reminder_text,
                time=reminder_time,
            )
        except Exception as e:
            logger.error("Failed to predict reminder time:", e)
            return ReminderSchema(
                user_id=user_id,
                text=reminder_text,
                time=timeutils.convert_utc_to_user_timezone(
                    timeutils.get_utc_now() + datetime.timedelta(minutes=30),
                    user.timezone_offset
                )
            )

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
