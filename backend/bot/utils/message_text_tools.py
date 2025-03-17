from collections.abc import Coroutine
from datetime import datetime

from backend.bot.clients.remindme_api import client


def get_message_reminder(data: dict):
    pass


def get_message_reminders(data: dict):
    reminders = sorted(client.get_reminders(data), key=lambda x: x["time_exp"])

    next_coef = data["next_coef"]

    strip = [index + 5 * next_coef for index in data['strip']]
    day = data["day"]

    text = "📝 *Напоминания* \n\n"

    day_emoji = {
        "today": "🏞",
        "tomorrow": "🌅",
        "all": "🌄"
    }

    day_dict = {
        "today": "Сегодня",
        "tomorrow": "Завтра",
        "all": "Все напоминания"
    }

    text += f"*{day_emoji[day]} {day_dict[day]}{"  ("+data["tag_filter"]+")" if data["tag_filter"] != None else ":"}*\n"

    added_lines_count = 0
    for id, reminder in enumerate(reminders):
        if id in range(*strip):
            if reminder["state"]:
                text += f"~{str(id + 1)}) {reminder['text'].capitalize()}~\n"
            else:
                text += f"{str(id + 1)}) {reminder['text'].capitalize()} ({reminder["time_exp"]})\n"
            added_lines_count += 1
    if not added_lines_count:
        text = ''.join(text.split("\n")[:-2]) + f"\n\n{day_emoji[day]} "
        if data["tag_filter"]:
            text += f"*Задач ({data["tag_filter"]}) нет.*\n"
        elif data["day_filter"] != "all":
            text += "*В этот день нет задач, можете отдыхать.*\n"
        else:
            text += f"*На {day_dict[day]} напоминаний нет.*\n"

    if added_lines_count:
        text += "\nВыбери напоминание для редактирования!"
    else:
        text += "Попробуй добавить новую задачу!"

    return (text.replace(")", "\)").replace(".", "\n").
            replace("-", "\-").replace("!", "\!")).replace("(", "\(")


def get_tags_edit(data: dict):
    text = "🔍 Ваши тэги:\n\n"

    tags = client.get_tags()
    dick = ["Ясность", "Кошки", "Знания", "Записки", "Идеи"]
    for i, tag in enumerate(tags):
        text += f"{i+1}\) {dick[i]}  {tag}\n"

    text += "\nВыберите тэг для редактирования:"

    return text


def get_message_habits(data: dict):
    habits = client.get_habits(data)

    today = datetime.now()
    current_month = today.strftime("%B")
    months_ru = {
        "January": "Январь",
        "February": "Февраль",
        "March": "Март",
        "April": "Апрель",
        "May": "Май",
        "June": "Июнь",
        "July": "Июль",
        "August": "Август",
        "September": "Сентябрь",
        "October": "Октябрь",
        "November": "Ноябрь",
        "December": "Декабрь"
    }

    text = "🎯 Ваши привычки:\n\n"
    for index, habit in enumerate(habits):
        text += "✅ " if habit["status"] else "❌ "

        text_progress = f"{months_ru[current_month]}" if habit["period"] == "month" else "неделю"
        text += f"{index+1}) {habit["habit_text"]} ({habit["progress"]} раз за {text_progress})\n"

    text += "\nВыберите привычку для редактирования:"
    return (text.replace(")", "\)").replace(".", "\n").
            replace("-", "\-").replace("!", "\!")).replace("(", "\(")
