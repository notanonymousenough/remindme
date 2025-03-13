from collections.abc import Coroutine

from backend.bot.clients.remindme_api import RemindMeApiClient


def get_message_reminders(data: dict):
    reminders = data["reminders"]
    next_coef = data["next_coef"]
    strip = [index + 5 * next_coef for index in data['strip']]
    day = data["day"]

    text = "📝 Напоминания \n\n"

    day_emoji = {
        "сегодня": "🏞",
        "завтра": "🌅",
        "остальные дни": "🌄"
    }
    text += f"{day_emoji[day] + day.capitalize()}\n"

    for id, reminder in enumerate(reminders):
        if id in range(*strip):
            if reminder["state"]:
                text += f"~{str(id + 1)}) {reminder['text']}\n~"
            else:
                text += f"{str(id + 1)}) {reminder['text']}\n"


    text += "\nВыбери напоминание для редактирования!"
    return text.replace(")", "\)").replace("-", "\-").replace("!", "\!")


def get_habits_message():
    pass
