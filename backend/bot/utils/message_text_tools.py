from typing import List

from backend.bot.utils.habit_tools import HABIT_PERIOD_NAMES, get_completed_record_sum, \
    get_last_record_status, HABIT_PERIOD_NAMES_INTERVAL
from backend.bot.utils.parse_markdown_text import parse_for_markdown
from backend.control_plane.schemas import ReminderSchema
from backend.control_plane.schemas.habit import HabitSchemaResponse


def get_reminder(reminder: ReminderSchema):
    text = (f"{reminder.text} {reminder.tag}:\n\n"
            f"   {reminder.time}")


def get_reminders(reminders, next_coef: int, strip: dict, day: str, tag_filter):
    strip = [index + 5 * next_coef for index in strip]

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

    text = f"*{day_emoji[day]} {day_dict[day]}{"  (" + tag_filter + ")" if tag_filter != None else ":"}*\n"

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


def get_tags(tags, new_tag: bool = False):
    text = "🔍 Ваши тэги:\n\n"

    for i, tag in enumerate(tags):
        text += f"{i + 1}) {tags[tag]["emoji"]}  – {tags[tag]["name"]}\n"
    if new_tag:
        text += "\nКакое эмодзи будет у нового тэга?"
    else:
        text += "\nВыберите тэг для редактирования:"

    return text


def get_habits(habits: List[HabitSchemaResponse]):
    text = "🎯 Ваши привычки:\n\n"

    for index, habit in enumerate(habits):
        text += f"{index + 1}. {habit.text}: ({get_completed_record_sum(habit=habit)} раз за {HABIT_PERIOD_NAMES[habit.interval]})\n"

    text += "Выберите привычку:"
    return parse_for_markdown(text)


def get_habit(habit: HabitSchemaResponse):
    text = (f'Привычка "{habit.text}":\n'
            f"    за {HABIT_PERIOD_NAMES[habit.interval]}: {get_completed_record_sum(habit=habit)} раз\n\n")

    text += (f"{HABIT_PERIOD_NAMES_INTERVAL[habit.interval].capitalize()} вы "
             f"{get_last_record_status(habit=habit)} привычку {get_last_record_status(habit=habit, emoji_flag=True)}")
    return parse_for_markdown(text)