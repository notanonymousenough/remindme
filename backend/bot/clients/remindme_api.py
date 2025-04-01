import uuid
from datetime import datetime, timedelta

from backend.bot.clients.http_client import AsyncHttpClient
from backend.control_plane.config import get_settings
from backend.control_plane.schemas.user import UserTelegramDataSchema
from backend.control_plane.utils import auth


class RemindMeApiClient(AsyncHttpClient):
    async def get_access_token(self, data):
        endpoint = "http://control-plane:8000/auth/telegram"

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

        return (await response.json())['access_token']

    def get_reminder(self, user):  # user: User
        endpoint = ""
        return {
            "id": 0,
            "text": "Помыть кота",
            "date_exp": "15.05.2025"
        }

    def get_reminders(self, day: str, tag_filter) -> list:  # user: User
        if day == "today":
            date_filter = datetime.now().strftime("%d.%m.%Y")
        elif day == "tomorrow":
            date_filter = (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y")
        else:
            date_filter = None

        data = {
            "reminders":
                [
                    {
                        "id": 0,
                        "text": "Помыть кота",
                        "date_exp": (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y"),
                        "time_exp": "14:48",
                        "state": 0,
                        "tag": "💡"
                    },
                    {
                        "id": 1,
                        "text": "Помыть cобаку",
                        "date_exp": date_filter,
                        "time_exp": "06:20",
                        "state": 1,
                        "tag": "💡"
                    },
                    {
                        "id": 2,
                        "text": "не сделать что-то",
                        "date_exp": (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y"),
                        "time_exp": "09:20",
                        "state": 0,
                        "tag": "💡"
                    },
                    {
                        "id": 3,
                        "text": "сделать что-то",
                        "date_exp": (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y"),
                        "time_exp": "14:20",
                        "state": 0,
                        "tag": "💡"
                    },
                    {
                        "id": 4,
                        "text": "не сделать что-то",
                        "date_exp": (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y"),
                        "time_exp": "13:20",
                        "state": 1,
                        "tag": "💡"
                    },
                    {
                        "id": 5,
                        "text": "не сделать что-то",
                        "date_exp": "13.03.2025",
                        "time_exp": "12:20",
                        "state": 1,
                        "tag": "📝"
                    },
                    {
                        "id": 6,
                        "text": "не сделать что-то",
                        "date_exp": "13.03.2025",
                        "time_exp": "16:20",
                        "state": 1,
                        "tag": "📝"
                    },
                    {
                        "id": 7,
                        "text": "не сделать что-то",
                        "date_exp": "13.03.2026",
                        "time_exp": "04:20",
                        "state": 0,
                        "tag": "🐈"
                    },
                    {
                        "id": 8,
                        "text": "задача с тегом кошечка",
                        "date_exp": "13.03.2027",
                        "time_exp": "04:20",
                        "state": 0,
                        "tag": "🐈"
                    },
                    {
                        "id": 9,
                        "text": "не сделать что-то",
                        "date_exp": "17.03.2025",
                        "time_exp": "11:20",
                        "state": 0,
                        "tag": ""
                    },
                    {
                        "id": 10,
                        "text": "не сделать что-то",
                        "date_exp": date_filter,
                        "time_exp": "04:20",
                        "state": 0,
                        "tag": ""
                    },
                    {
                        "id": 11,
                        "text": "не сделать что-то",
                        "date_exp": "13.03.2025",
                        "time_exp": "04:20",
                        "state": 0,
                        "tag": ""
                    },
                    {
                        "id": 12,
                        "text": "предпоследний",
                        "date_exp": "14.03.2025",
                        "time_exp": "04:20",
                        "state": 0,
                        "tag": ""
                    },
                    {
                        "id": 13,
                        "text": "последний",
                        "date_exp": "14.03.2025",
                        "time_exp": "04:20",
                        "state": 0,
                        "tag": ""
                    }
                ]
        }

        return [
            reminder for reminder in data["reminders"]
            if (date_filter is None or reminder["date_exp"] == date_filter)
               and (tag_filter is None or reminder["tag"] == tag_filter)
        ]

    def get_tags(self):
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
