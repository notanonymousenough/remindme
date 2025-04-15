import enum
import logging
import uuid
from datetime import datetime, timedelta
from typing import Union, Sequence

import aiohttp

from backend.bot.clients.http_client import AsyncHttpClient
from backend.control_plane.config import get_settings
from backend.control_plane.schemas.habit import HabitSchemaResponse
from backend.control_plane.schemas.requests.habit import HabitSchemaPostRequest, HabitProgressSchemaPostRequest
from backend.control_plane.schemas.requests.reminder import ReminderAddSchemaRequest
from backend.control_plane.schemas.requests.tag import TagRequestSchema
from backend.control_plane.schemas.tag import TagSchema
from backend.control_plane.schemas.user import UserTelegramDataSchema
from backend.control_plane.service.habit_service import get_habit_service
from backend.control_plane.service.tag_service import get_tag_service


class REQUEST_METHODS(str, enum.Enum):
    POST = "POST"
    GET = "GET"
    PUT = "PUT"
    DELETE = "DELETE"


# REQUEST_METHODS = ["POST", "GET", "PUT", "DELETE"]


class RemindMeApiClient(AsyncHttpClient):
    async def create_request(self, endpoint: str, method: REQUEST_METHODS, access_token: str, request_body=None) -> \
            Union[dict, None]:
        await self._create_session()
        SESSION_REQUEST_METHODS = {
            key: getattr(self._session, key.lower()) for key in REQUEST_METHODS
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            'accept': "application/json",
            "Content-Type": "application/json"
        }

        request_kwargs = {
            "url": endpoint,
            "headers": headers
        }
        if request_body:
            request_kwargs.update(data=request_body.model_dump_json())

        http_method = SESSION_REQUEST_METHODS[method]
        try:
            response = await http_method(
                **request_kwargs
            )

        except Exception as ex:
            print(f"api response error: {ex}")
            await self._close_session()
            raise ex
        if response.status != 200:
            print("api response status ERROR:", (await response.status))
            await self._close_session()
            return None

        response_json = await response.json()
        await self._close_session()

        return response_json

    async def get_access_token(self, request: UserTelegramDataSchema) -> Union[str, None]:
        await self._create_session()
        endpoint = get_settings().GET_ACCESS_TOKEN_ENDPOINT

        headers = {
            'accept': "application/json",
            "Content-Type": "application/json"
        }

        response = await self._session.post(
            headers=headers,
            url=endpoint,
            data=request.model_dump_json()
        )
        if response.status != 200:
            print("api response error:", (await response.json()))
            return None

        access_token = (await response.json())['access_token']

        await self._close_session()
        return access_token

    async def reminder_get(self, access_token: str, reminder_id: int):
        await self._create_session()
        endpoint = ""

        headers = {
            'accept': "application/json",
            "Content-Type": "application/json"
        }

        await self._close_session()
        return {
            "id": 0,
            "text": "Помыть кота",
            "date_exp": "15.05.2025"
        }

    async def reminder_post(self, access_token: str, request: ReminderAddSchemaRequest):
        await self._create_session()

        endpoint = "/v1/reminder/"

        headers = {
            "Authorization": f"Bearer {access_token}",
            'accept': "application/json",
            "Content-Type": "application/json"
        }

        response = await self._session.post(
            url=endpoint,
            headers=headers,
            data=request.model_dump_json()
        )
        await self._close_session()

        return True if response.status == 200 else False

    @staticmethod
    async def tag_put(request: TagRequestSchema, tag_id: str) -> bool:
        return await get_tag_service().update_tag(tag_id=tag_id, request=request)

    @staticmethod
    async def tag_get(tag_id: str) -> Union[TagSchema, bool]:
        try:
            tag = await get_tag_service().tag_get(uuid.UUID(tag_id))
            return tag
        except Exception as ex:
            print(f"Ошибка: {ex}")
            return False

    async def tag_post(self, access_token: str, request: TagRequestSchema) -> bool:
        await self._create_session()

        endpoint = "/v1/tag/"

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

        endpoint = "/v1/reminder/"

        headers = {
            "Authorization": f"Bearer {state_data["access_token"]}"
        }

        response = await self._session.get(
            url=endpoint,
            headers=headers
        )
        reminders = (await response.json())
        await self._close_session()

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

    async def tags_get(self, state_data: dict) -> Union[Sequence[dict], None]:
        await self._create_session()
        endpoint = "/v1/tag/"

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
            print(f"Ошибка при получении тегов: {e}")
            return {}  # Или raise e чтобы пробросить ошибку выше

        await self._close_session()

        tags = {
            tag["id"]: {
                "name": tag["name"],
                "emoji": tag['emoji']
            } for tag in response_json
        }

        return tags

    async def habits_get(self, state_data: dict):
        await self._create_session()
        endpoint = "/v1/habit/"

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
        endpoint = "/v1/habit/"

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

    @staticmethod
    async def habit_get(habit_id: uuid.UUID) -> HabitSchemaResponse:
        habit_service = get_habit_service()
        habit = await habit_service.habit_get(habit_id)
        return habit

    async def habit_progress_post(self, access_token: str, habit_id: uuid.UUID) -> bool:
        endpoint = f"/v1/habit/{str(habit_id)}/progress"
        if await self.create_request(
                endpoint=endpoint,
                method=REQUEST_METHODS.POST,
                access_token=access_token,
                request_body=HabitProgressSchemaPostRequest.model_validate({'habit_id': habit_id})
        ):
            return True
        return False

    @staticmethod
    async def habit_progress_delete_last(habit_id: uuid.UUID) -> bool:
        return await get_habit_service().habit_progress_delete_last_record(habit_id)


_client = None


async def get_client_async():
    global _client
    if not _client:
        _client = RemindMeApiClient()
    return _client
