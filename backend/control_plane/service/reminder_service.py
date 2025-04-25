import datetime
import logging
from typing import Sequence
from uuid import UUID

from backend.control_plane.ai_clients import default_llm_ai_provider
from backend.control_plane.ai_clients.prompts import RequestType
from backend.control_plane.db.models import ReminderStatus
from backend.control_plane.db.repositories.reminder import ReminderRepository
from backend.control_plane.db.repositories.user import UserRepository
from backend.control_plane.exceptions.quota import QuotaExceededException
from backend.control_plane.schemas import ReminderSchema
from backend.control_plane.schemas.requests.reminder import ReminderToEditRequestSchema, \
    ReminderMarkAsCompleteRequestSchema, ReminderToEditTimeRequestSchema, ReminderAddSchemaRequest
from backend.control_plane.service.quota_service import get_quota_service
from backend.control_plane.service.tag_service import get_tag_service
from backend.control_plane.utils import timeutils

logger = logging.getLogger("reminder_service")


class RemindersService:
    def __init__(self):
        self.repo = ReminderRepository()
        self.user_repo = UserRepository()
        self.quota_service = get_quota_service()
        self.ai_provider = default_llm_ai_provider

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
            return await self.create_with_ai_predicted_time(user_id=user_id, reminder_text=reminder.text)
        # Otherwise create reminder in DB and return it
        user = await self.user_repo.get_user(user_id)
        reminder.time = timeutils.convert_user_timezone_to_utc(reminder.time, user.timezone_offset)

        request = reminder.model_dump(exclude_unset=True, exclude_none=True)
        return await self.repo.reminder_create(user_id=user_id, reminder=request)

    async def create_with_ai_predicted_time(self, user_id: UUID, reminder_text: str) -> ReminderSchema:
        user = await self.user_repo.get_user(user_id=user_id)
        try:
            # Проверяем лимиты
            await self.quota_service.check_ai_llm_request_limit(
                user_id,
                RequestType.PREDICT_REMINDER_TIME,
                reminder_text
            )

            # Запрашиваем предсказание времени
            reminder_time, token_count = await self.ai_provider.predict_reminder_time(
                user.timezone_offset,
                reminder_text
            )

            # Обновляем использование ресурсов
            await self.quota_service.update_ai_llm_request_usage(
                user_id,
                RequestType.PREDICT_REMINDER_TIME,
                token_count
            )

            return ReminderSchema(
                user_id=user_id,
                text=reminder_text,
                time=reminder_time,
            )
        except QuotaExceededException as e:
            logger.warning(f"Quota exceeded: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to predict reminder time: {str(e)}")
            # TODO: mark answer as non-ai-predicted
            # TODO: time_matches = re.findall(r'(в \d{1,2}:\d{2}|через \d+ час(ов|а)?|завтра|послезавтра)', task_text, re.IGNORECASE)
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
