import logging
from datetime import datetime, timedelta
from typing import Union, Sequence
from uuid import UUID

import aiohttp

from backend.bot.clients.http_client import AsyncHttpClient, REQUEST_METHODS
from backend.control_plane.config import get_settings
from backend.control_plane.db.models import ReminderStatus
from backend.control_plane.schemas import ReminderSchema
from backend.control_plane.schemas.habit import HabitSchemaResponse
from backend.control_plane.schemas.requests.habit import HabitSchemaPostRequest, HabitProgressSchemaPostRequest
from backend.control_plane.schemas.requests.reminder import ReminderPostRequest, ReminderEditTimeRequest, \
    ReminderCompleteRequest, ReminderEditNameRequest
from backend.control_plane.schemas.requests.tag import TagRequestSchema
from backend.control_plane.schemas.tag import TagSchema
from backend.control_plane.schemas.user import UserTelegramDataSchema, UserSchema
from backend.control_plane.service.habit_service import get_habit_service
from backend.control_plane.service.reminder_service import get_reminder_service
from backend.control_plane.service.tag_service import get_tag_service


class RemindMeApiClient(AsyncHttpClient):
    async def registrate_timezone(self, request) -> UserSchema:
        endpoint = get_settings().USER_UPDATE_ENDPOINT
        response = await self.create_request(
            endpoint=endpoint,
            request_body=request,
            method=REQUEST_METHODS.POST
        )
        return UserSchema.model_validate(response)

    async def get_access_token(self, request: UserTelegramDataSchema) -> Union[str, None]:
        endpoint = get_settings().GET_ACCESS_TOKEN_ENDPOINT
        response = await self.create_request(
            endpoint=endpoint,
            request_body=request,
            method=REQUEST_METHODS.POST
        )
        access_token = response['access_token']
        return access_token

    async def reminder_complete(self, access_token: str, reminder_id: UUID, status: ReminderStatus) -> bool:
        """
        МЕНЯЕТ СТАТУС У НАПОМИНАНИЯ
        """
        endpoint = get_settings().COMPLETE_REMINDER_ENDPOINT.format(id=reminder_id)

        if status == ReminderStatus.COMPLETED:
            new_status = ReminderStatus.ACTIVE
        else:
            new_status = ReminderStatus.COMPLETED

        request_body = ReminderCompleteRequest.model_validate(
            {
                "id": reminder_id,
                "status": new_status
            }
        )
        response = await self.create_request(
            endpoint,
            REQUEST_METHODS.PUT,
            access_token,
            request_body
        )
        if response:
            return True
        return False

    @staticmethod
    async def reminder_get(access_token: str, reminder_id: UUID) -> ReminderSchema:
        """endpoint = get_settings().GET_REMINDER_ENDPOINT.format(id=reminder_id)
        response = await self.create_request(
            endpoint,
            REQUEST_METHODS.GET,
            access_token
        )
        return ReminderSchema.model_validate(response)"""
        reminder_service = get_reminder_service()
        reminder = await reminder_service.reminder_get(reminder_id)

        reminder_tags = await get_tag_service().get_tags_info_from_reminder_id(reminder_id=reminder.id)
        reminder.tags = reminder_tags  # TAG SCHEMA # TODO fix or delete

        return reminder

    async def change_reminder_tags(
            self,
            access_token: str,
            reminder_id: UUID,
            tag_to_add: UUID = None,
            tag_to_delete: UUID = None
    ):
        if tag_to_delete:
            await get_tag_service().delete_tags_from_reminder(reminder_id=reminder_id,
                                                              tag_ids_to_delete=[tag_to_delete])
        if tag_to_add:
            await get_tag_service().add_links(reminder_id, [tag_to_add])

    async def reminder_post(self, access_token: str, request: ReminderPostRequest) -> bool:
        endpoint = get_settings().POST_REMINDER_ENDPOINT

        if await self.create_request(
                endpoint,
                REQUEST_METHODS.POST,
                access_token,
                request_body=request
        ):
            return True
        logging.info(f"request: {request} \nReminder Post failed")
        return False

    async def reminder_postpone(self, access_token: str, request: ReminderEditTimeRequest) -> bool:
        endpoint = get_settings().POSTPONE_REMINDER_ENDPOINT.format(id=request.id)
        if await self.create_request(
                endpoint,
                REQUEST_METHODS.PUT,
                access_token=access_token,
                request_body=request
        ):
            return True
        return False

    async def reminder_put(self,
                           access_token: str,
                           request: ReminderEditNameRequest):
        endpoint = get_settings().PUT_REMINDER_ENDPOINT.format(id=request.id)
        if await self.create_request(
                endpoint,
                REQUEST_METHODS.PUT,
                access_token=access_token,
                request_body=request
        ):
            return True
        return False

    @staticmethod
    async def tag_put(request: TagRequestSchema, tag_id: str) -> bool:
        return await get_tag_service().update_tag(tag_id=tag_id, request=request)

    @staticmethod
    async def tag_get(tag_id: str) -> Union[TagSchema, bool]:
        try:
            tag = await get_tag_service().tag_get(UUID(tag_id))
            return tag
        except Exception as ex:
            print(f"Ошибка: {ex}")
            return False

    async def tag_post(self, access_token: str, request: TagRequestSchema) -> bool:
        await self._create_session()

        endpoint = get_settings().POST_TAG_ENDPOINT

        headers = {
            "Authorization": f"Bearer {access_token}",
            'accept': "application/json",
            "Content-Type": "application/json"
        }

        try:
            response = await self._session.post(
                url=endpoint,
                headers=headers,
                data=request.model_dump_json()
            )
            if response.status == 200:
                await self._close_session()
                return True
            await self._close_session()
            return False
        except Exception as ex:
            print(f"{ex} ошибка при отправке за сервер.")
            await self._close_session()
            return False

    async def reminders_get(self, state_data) -> list:
        await self._create_session()

        endpoint = get_settings().GET_REMINDERS_ENDPOINT

        access_token = state_data["access_token"]
        reminders = await self.create_request(
            endpoint,
            REQUEST_METHODS.GET,
            access_token=access_token
        )

        day, tag_emoji_filter = state_data["day"], state_data["tag_filter"]
        if day == "today":
            date_filter = datetime.now().strftime("%d.%m.%Y")
        elif day == "tomorrow":
            date_filter = (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y")
        else:
            date_filter = None

        logging.info(f"response: {reminders}")

        for reminder in reminders:
            reminder_tags = await get_tag_service().get_tags_info_from_reminder_id(reminder_id=reminder['id'])
            reminder['tags'] = reminder_tags  # TAG SCHEMA

        reminders = [
            reminder for reminder in reminders
            if (date_filter is None or datetime.fromisoformat(reminder["time"]).strftime("%d.%m.%Y") == date_filter)
               and (tag_emoji_filter is None or (reminder["tags"] and
                                                 tag_emoji_filter in [tag.emoji for tag in reminder["tags"]]))
        ]
        return reminders

    async def tags_get(self, access_token: str) -> Union[Sequence[TagSchema], None]:
        endpoint = get_settings().GET_TAGS_ENDPOINT
        response = await self.create_request(
            endpoint,
            REQUEST_METHODS.GET,
            access_token=access_token,
        )
        tag_schema = [TagSchema.model_validate(tag) for tag in response]
        return tag_schema

    async def habits_get(self, state_data: dict):
        await self._create_session()
        endpoint = get_settings().GET_HABITS_ENDPOINT

        headers = {
            "Authorization": f"Bearer {state_data["access_token"]}"
        }

        response = await self._session.get(
            url=endpoint,
            headers=headers
        )

        try:
            response.raise_for_status()
            response_json = (await response.json())
        except aiohttp.ClientError as e:
            await self._close_session()
            print(f"Ошибка при получении привычек: {e}")
            return {}

        await self._close_session()
        habits = [HabitSchemaResponse.model_validate(model) for model in response_json]
        return habits

    async def habit_post(self, state_data: dict, habit_request: HabitSchemaPostRequest) -> bool:
        await self._create_session()
        endpoint = get_settings().POST_HABIT_ENDPOINT

        headers = {
            "Authorization": f"Bearer {state_data["access_token"]}",
            'accept': "application/json",
            "Content-Type": "application/json"
        }

        response = await self._session.post(
            url=endpoint,
            headers=headers,
            data=habit_request.model_dump_json()
        )

        try:
            response.raise_for_status()
        except aiohttp.ClientError as e:
            await self._close_session()
            print(f"Exception in habit post: {e}")
            return False

        await self._close_session()
        return True if response.status == 200 else False

    async def habit_delete(self, access_token: str, habit_id: UUID) -> bool:
        await self._create_session()
        endpoint = get_settings().DELETE_HABIT_ENDPOINT.format(id=habit_id)

        if await self.create_request(
                endpoint=endpoint,
                method=REQUEST_METHODS.DELETE,
                access_token=access_token,
        ):
            return True
        return False

    @staticmethod
    async def habit_get(habit_id: UUID) -> HabitSchemaResponse:
        habit_service = get_habit_service()
        response = await habit_service.habit_get(model_id=habit_id)
        return HabitSchemaResponse.model_validate(response)

    async def habit_progress_post(self, access_token: str, habit_id: UUID) -> bool:
        endpoint = get_settings().POST_HABIT_PROGRESS_ENDPOINT.format(id=habit_id)
        if await self.create_request(
                endpoint=endpoint,
                method=REQUEST_METHODS.POST,
                access_token=access_token,
                request_body=HabitProgressSchemaPostRequest.model_validate({'habit_id': habit_id})
        ):
            return True
        return False

    @staticmethod
    async def habit_progress_delete_last(habit_id: UUID) -> bool:
        return await get_habit_service().habit_progress_delete_last_record(habit_id)

    async def user_get(self, access_token: str):
        endpoint = get_settings().GET_USER
        response = await self.create_request(
            endpoint=endpoint,
            method=REQUEST_METHODS.GET,
            access_token=access_token
        )
        return UserSchema.model_validate(response)


_client = None


async def get_client_async():
    global _client
    if not _client:
        _client = RemindMeApiClient()
    return _client
