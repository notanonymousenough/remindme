import logging
import uuid
from datetime import datetime, timedelta
from typing import Union

from backend.bot.clients.http_client import AsyncHttpClient
from backend.control_plane.config import get_settings
from backend.control_plane.service.reminder_service import get_reminder_service
from backend.control_plane.service.tag_service import get_tag_service

from backend.control_plane.utils import auth


class RemindMeApiClient(AsyncHttpClient):
    async def get_access_token(self, data_telegram_auth: dict) -> Union[str, None]:
        await self._create_session()
        #  endpoint = get_settings().GET_ACCESS_TOKEN_ENDPOINT
        endpoint = "/auth/telegram"

        request_data = {  # from scheme/telegram_scheme
            "telegram_id": str(data_telegram_auth["telegram_id"]),
            "first_name": data_telegram_auth["first_name"],
            "last_name": data_telegram_auth["last_name"],
            "username": data_telegram_auth["username"],
            "photo_url": None,
            "auth_date": str(datetime.now()),
            "hash": auth.generate_hash(data_telegram_auth)
        }

        response = await self._session.post(
            url=endpoint,
            json=request_data
        )
        if response.status != 200:
            print("api response error:", (await response.json()))
            return None

        access_token = (await response.json())['access_token']

        await self._close_session()
        return access_token

    async def get_reminder(self, user):  # user: User
        await self._create_session(base_url="")
        endpoint = ""
        return {
            "id": 0,
            "text": "Помыть кота",
            "date_exp": "15.05.2025"
        }

    async def get_reminders(self, state_data) -> list:  # user: User
        await self._create_session()  # TODO() get from config

        endpoint = "/reminder"

        headers = {
            "Authorization": f"Bearer {state_data["access_token"]}"
        }

        response = await self._session.get(
            url=endpoint,
            headers=headers
        )

        day, tag_filter = state_data["day"], state_data["tag_filter"]
        if day == "today":
            date_filter = datetime.now().strftime("%d.%m.%Y")
        elif day == "tomorrow":
            date_filter = (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y")
        else:
            date_filter = None

            """ 
            "date_exp": (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y"),
            "tag": *emoji*
            """

        reminders = (await response.json())
        logging.info(f"response: {reminders}")

        await self._close_session()

        for reminder in reminders:
            tags_id = get_tag_service().get_links_tags_reminders(reminder["id"])

            emoji_tags = None  # TODO emoji_list from tags_id
            if tags_id:
                reminder["tags"] = emoji_tags

        reminders = [
            reminder for reminder in reminders
            if (date_filter is None or datetime.fromisoformat(reminder["time"]).strftime(
                "%d.%m.%Y") == date_filter)  # тут надо дату
               and (tag_filter is None or reminder["tags"] == tag_filter)
        ]
        return reminders

    async def get_tags(self, state_data):
        await self._create_session()
        endpoint = "/tag"  # TODO

        headers = {
            "Authorization": f"Bearer {state_data["access_token"]}"
        }

        response = await self._session.get(
            url=endpoint,
            headers=headers
        )

        response_json = (await response.json())

        tags_id = None  # TODO
        tags_name = [tag['name'] for tag in response_json]
        tags_emoji = [tag["emoji"] for tag in response_json]

        dict_tags = {
            uuid.uuid4(): {
                "name": tag_name,
                "emoji": tag_emoji
            }
            for tag_name, tag_emoji in zip(tags_name, tags_emoji)
        }
        return dict_tags

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
