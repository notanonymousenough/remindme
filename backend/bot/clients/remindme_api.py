import logging
import uuid
from datetime import datetime, timedelta
from typing import Union, Sequence

import aiohttp

from backend.bot.clients.http_client import AsyncHttpClient
from backend.control_plane.config import get_settings
from backend.control_plane.schemas.requests.reminder import ReminderAddSchemaRequest
from backend.control_plane.schemas.requests.tag import TagRequestSchema
from backend.control_plane.schemas.tag import TagSchema
from backend.control_plane.schemas.user import UserTelegramDataSchema
from backend.control_plane.service.tag_service import get_tag_service


class RemindMeApiClient(AsyncHttpClient):
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

    async def get_reminder(self, access_token: str, reminder_id: int):
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

    async def post_reminder(self, access_token: str, request: ReminderAddSchemaRequest):
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
    async def edit_tag(request: TagRequestSchema, tag_id: str) -> bool:
        return await get_tag_service().update_tag(tag_id=tag_id, request=request)

    @staticmethod
    async def get_tag(tag_id: str) -> Union[TagSchema, bool]:
        try:
            tag = await get_tag_service().get_tag(uuid.UUID(tag_id))
            return tag
        except Exception as ex:
            print(f"Ошибка: {ex}")
            return False

    async def post_tag(self, access_token: str, request: TagRequestSchema) -> bool:
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

    async def get_reminders(self, state_data) -> list:
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

    async def get_tags(self, state_data: dict) -> Union[Sequence[dict], None]:
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

    def get_habits(self, data: dict):
        return [
            {
                "user_id": data["user_id"],
                "habit_id": 0,
                "habit_text": "Уход за лицом",
                "status": 0,
                "period": "month",
                "progress": 3
            },
            {
                "user_id": data["user_id"],
                "habit_id": 1,
                "habit_text": "Бегать 100 метровку",
                "status": 1,
                "period": "weekly",
                "progress": 6
            }
        ]


_client = None


async def get_client_async():
    global _client
    if not _client:
        _client = RemindMeApiClient()
    return _client
