from datetime import datetime, timedelta

from backend.bot.clients.http_client import AsyncHttpClient
from backend.bot.remindmeapi.models.user import User


class RemindMeApiClient(AsyncHttpClient):
    def get_reminder(self, user):  # user: User
        # database controller..
        return {
            "id": 0,
            "text": "Помыть кота",
            "date_exp": "15.05.2025"
        }

    def get_reminders(self, user, day: str) -> list:  # user: User
        if day == "сегодня":
            date_filter = datetime.now().strftime("%d.%m.%Y")
        elif day == "завтра":
            date_filter = (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y")
        else:
            date_filter = None

        data = {
            "reminders":
                [
                    {
                        "id": 0,
                        "text": "Помыть кота",
                        "date_exp": date_filter,
                        "state": 0
                    },
                    {
                        "id": 1,
                        "text": "Помыть cобаку",
                        "date_exp": date_filter,
                        "state": 1
                    },
                    {
                        "id": 2,
                        "text": "не сделать что-то",
                        "date_exp": date_filter,
                        "state": 0
                    },
                    {
                        "id": 3,
                        "text": "сделать что-то",
                        "date_exp": "22.05.2025",
                        "state": 0
                    },
                    {
                        "id": 4,
                        "text": "не сделать что-то",
                        "date_exp": date_filter,
                        "state": 1
                    },
                    {
                        "id": 5,
                        "text": "не сделать что-то",
                        "date_exp": date_filter,
                        "state": 1
                    },
                    {
                        "id": 6,
                        "text": "не сделать что-то",
                        "date_exp": date_filter,
                        "state": 1
                    },
                    {
                        "id": 7,
                        "text": "не сделать что-то",
                        "date_exp": date_filter,
                        "state": 0
                    },
                    {
                        "id": 8,
                        "text": "не сделать что-то",
                        "date_exp": date_filter,
                        "state": 0
                    },
                    {
                        "id": 9,
                        "text": "не сделать что-то",
                        "date_exp": date_filter,
                        "state": 0
                    },
                    {
                        "id": 10,
                        "text": "не сделать что-то",
                        "date_exp": date_filter,
                        "state": 0
                    },
                    {
                        "id": 11,
                        "text": "не сделать что-то",
                        "date_exp": date_filter,
                        "state": 0
                    },
                    {
                        "id": 12,
                        "text": "предпоследний",
                        "date_exp": date_filter,
                        "state": 0
                    },
                    {
                        "id": 13,
                        "text": "последний",
                        "date_exp": date_filter,
                        "state": 0
                    }
                ]
        }
        return [reminder for reminder in data["reminders"] if date_filter is None or reminder["date_exp"] == date_filter]


client = RemindMeApiClient()
