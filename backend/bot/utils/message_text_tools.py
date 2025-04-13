from datetime import datetime
from typing import List

from backend.bot.utils.parse_markdown_text import parse_for_markdown
from backend.control_plane.db.models import HabitPeriod
from backend.control_plane.schemas.habit import HabitSchemaResponse

HABIT_PERIOD_NAMES = {
    HabitPeriod.DAILY: "месяц",
    HabitPeriod.WEEKLY: "полгода",
    HabitPeriod.MONTHLY: "год"
}

HABIT_PERIOD_NAMES_INTERVAL = {
    HabitPeriod.DAILY: "сегодня",
    HabitPeriod.WEEKLY: "на этой неделе",
    HabitPeriod.MONTHLY: "в этом месяце"
}

STATUS_EMOJI = {
    False: "❌",
    True: "✅"
}

def get_message_reminder(reminder):
    pass


def get_message_reminders(reminders, next_coef: int, strip: dict, day: str, tag_filter):
    strip = [index + 5 * next_coef for index in strip]

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

    text += f"*{day_emoji[day]} {day_dict[day]}{"  (" + tag_filter + ")" if tag_filter != None else ":"}*\n"

    added_lines_count = 0
    for id, reminder in enumerate(reminders):
        if id in range(*strip):
            if reminder["status"] == "complete":  # выполнено - strike
                text += f"~{str(id + 1)}) {reminder['text'].capitalize()}~\n"
            else:
                text += f"{str(id + 1)}) {reminder['text'].capitalize()} ({reminder["time"]})\n"
            added_lines_count += 1

    if not added_lines_count:
        text = ''.join(text.split("\n")[:-2]) + f"\n\n{day_emoji[day]} "
        if tag_filter:
            text += f"*Задач ({tag_filter}) нет.*\n"
        elif tag_filter != "all":
            text += "*В этот день нет задач, можете отдыхать.*\n"
        else:
            text += f"*На {day_dict[day]} напоминаний нет.*\n"

    if added_lines_count:
        text += "\nВыбери напоминание для редактирования!"
    else:
        text += "Попробуй добавить новую задачу!"

    return parse_for_markdown(text)


def get_message_tags(tags, new_tag: bool = False):
    text = "🔍 Ваши тэги:\n\n"

    for i, tag in enumerate(tags):
        text += f"{i + 1}) {tags[tag]["emoji"]}  – {tags[tag]["name"]}\n"
    if new_tag:
        text += "\nКакое эмодзи будет у нового тэга?"
    else:
        text += "\nВыберите тэг для редактирования:"

    return text


def get_message_habits(habits: List[HabitSchemaResponse]):
    text = "🎯 Ваши привычки:\n\n"

    def get_completed_record_sum():
        return sum(record["completed"] for record in habit.progress)

    def get_last_record_status():
        status = habit.progress[-1]["completed"]
        return STATUS_EMOJI[status]

    for index, habit in enumerate(habits):
        text += (f"{index + 1}) {habit.text}:\n"
                 f"    Выполнено за {HABIT_PERIOD_NAMES[habit.interval]}: {get_completed_record_sum()} раз\n"
                 f"    Выполнено {HABIT_PERIOD_NAMES_INTERVAL[habit.interval]}: {get_last_record_status()}\n\n")

    text += "Выберите привычку для редактирования:"
    return parse_for_markdown(text)
