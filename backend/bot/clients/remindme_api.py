import logging
import uuid
from datetime import datetime, timedelta

from backend.bot.clients.http_client import AsyncHttpClient
from backend.control_plane.config import get_settings

from backend.control_plane.utils import auth


class RemindMeApiClient(AsyncHttpClient):
    async def get_access_token(self, data):
        await self._create_session()
        #  endpoint = get_settings().GET_ACCESS_TOKEN_ENDPOINT
        endpoint = "/auth/telegram"
        request_data = {  # from scheme/telegram_scheme
            "telegram_id": str(data["telegram_id"]),
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "username": data["username"],
            "photo_url": None,
            "auth_date": str(datetime.now()),
            "hash": auth.generate_hash(data)
        }
        # request = UserTelegramDataSchema(**request_data)

        response = await self._session.post(
            url=endpoint,
            json=request_data
        )
        if response.status != 200:
            print("api response error:", (await response.json()))
            return
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
            """

        data = (await response.json())
        logging.info(f"response: {data}")

        await self._close_session()
        return [
            reminder for reminder in data
            if (date_filter is None or reminder["time"] == date_filter)  # тут надо дату
               and (tag_filter is None or reminder["tag"] == tag_filter)
        ]

    def get_tags(self):
        endpoint = None  # TODO
        tags_example_naming = ["Ясность", "Кошки", "Знания", "Записки", "Идеи"]
        tags_example_emoji = ["☺️", "🐈", "📚", "📝", "💡"]
        dict_tags_example = {
            uuid.uuid4(): {
                "name": tag_name,
                "emoji": tag_emoji
            }
            for tag_name, tag_emoji in zip(tags_example_naming, tags_example_emoji)
        }
        return dict_tags_example

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


async def get_client():
    return RemindMeApiClient()
