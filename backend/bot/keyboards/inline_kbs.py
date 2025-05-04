from typing import Sequence, List

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from backend.bot.utils.habit_tools import get_last_record_status_bool
from backend.control_plane.config import get_settings
from backend.control_plane.db.models import ReminderStatus
from backend.control_plane.schemas.habit import HabitSchemaResponse


def reminder_datetime(reminder):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Поменять дату", callback_data="reminder_edit_datetime_date_"))
    keyboard.add(InlineKeyboardButton(text="Изменить время", callback_data="reminder_edit_datetime_time"))
    keyboard.row(InlineKeyboardButton(text="Назад", callback_data=f"reminder_edit_{reminder.id}"))

    return keyboard.as_markup()


def edit_reminder(reminder, mode: List[str], tags: List[dict] = None):
    if "datetime" in mode:
        return reminder_datetime(reminder)

    keyboard = InlineKeyboardBuilder()
    if reminder.status == ReminderStatus.ACTIVE:
        keyboard.row(InlineKeyboardButton(text="Выполнить", callback_data=f"reminder_edit_complete_{reminder.id}"))
    if reminder.status == ReminderStatus.COMPLETED:
        keyboard.row(
            InlineKeyboardButton(text="Отменить выполнение", callback_data=f"reminder_edit_complete_{reminder.id}"))
    keyboard.row(
        InlineKeyboardButton(text="Изменить дату и время", callback_data=f"reminder_edit_datetime_{reminder.id}"))

    if "tag" in mode:
        reminder_tags_emoji = []
        if reminder.tags:
            reminder_tags_emoji = [tag.emoji for tag in reminder.tags]

        keyboard.row(InlineKeyboardButton(text="<-", callback_data=f"reminder_edit_{reminder.id}"))

        for tag_id in tags:
            tag = tags[tag_id]

            if tag['emoji'] in reminder_tags_emoji:
                keyboard.add(InlineKeyboardButton(text=f"__{tag['emoji']}__", callback_data=f"reminder_edit_tag_change_{tag_id}"))
            else:
                keyboard.add(InlineKeyboardButton(text=f"{tag['emoji']}", callback_data=f"reminder_edit_tag_change_{tag_id}"))
    else:
        keyboard.row(InlineKeyboardButton(text="Изменить тэг", callback_data=f"reminder_edit_tag_{reminder.id}"))
    keyboard.row(InlineKeyboardButton(text="Переименовать", callback_data=f"reminder_edit_rename_{reminder.id}"))

    return keyboard.as_markup()


def get_habit_edit_buttons(habit: HabitSchemaResponse):
    keyboard = InlineKeyboardBuilder()

    if get_last_record_status_bool(habit=habit):
        keyboard.row(InlineKeyboardButton(text="Отменить выполнение", callback_data=f"habit_complete_False_{habit.id}"))
    else:
        keyboard.row(InlineKeyboardButton(text="Выполнить", callback_data=f"habit_complete_True_{habit.id}"))
    keyboard.row(InlineKeyboardButton(text="Переименовать", callback_data=f"habit_edit_name_{habit.id}"))
    keyboard.row(InlineKeyboardButton(text="Удалить", callback_data=f"habit_delete_{habit.id}"))

    return keyboard.as_markup()


def get_habits_buttons(habits: List[HabitSchemaResponse], next_coef: int):
    keyboard = InlineKeyboardBuilder()

    count_of_habits = len(habits)
    increase = 5 * next_coef

    start_index = increase
    end_index = min(start_index + 5, count_of_habits)

    if start_index > 1:
        keyboard.add(InlineKeyboardButton(text="<-", callback_data=f"habit_previous_{next_coef - 1}"))

    for index in range(start_index, end_index):
        habit_id = habits[index].id
        keyboard.add(InlineKeyboardButton(text=str(index + 1), callback_data=f"habit_edit_{habit_id}"))

    if end_index < count_of_habits:
        keyboard.add(InlineKeyboardButton(text="->", callback_data=f"habit_next_{next_coef + 1}"))

    return keyboard.as_markup()


def reminders_buttons(reminders, next_coef: int, day_filter: str, tag_filter_is_click: bool, tags):
    keyboard = InlineKeyboardBuilder()

    count_of_reminders = len(reminders)
    increase = 5 * next_coef

    start_index = increase
    end_index = min(start_index + 5, count_of_reminders)

    if start_index > 1:
        keyboard.row(InlineKeyboardButton(text="<-", callback_data=f"reminder_previous_{next_coef - 1}"))

    for index in range(start_index, end_index):
        reminder_id = reminders[index]['id']
        keyboard.row(InlineKeyboardButton(text=str(index + 1), callback_data=f"reminder_edit_{reminder_id}"))

    if end_index < count_of_reminders:
        keyboard.row(InlineKeyboardButton(text="->", callback_data=f"reminder_next_{next_coef + 1}"))

    keyboard.adjust(7)

    keyboard.row(InlineKeyboardButton(text=f"✅ Сегодня" if day_filter == "today" else "Сегодня",
                                      callback_data="reminder_day_filter_today"))
    keyboard.add(InlineKeyboardButton(text="✅ Завтра" if day_filter == "tomorrow" else "Завтра",
                                      callback_data="reminder_day_filter_tomorrow"))
    keyboard.add(InlineKeyboardButton(text="✅ ВСЕ" if day_filter == "all" else "Остальные дни",
                                      callback_data="reminder_day_filter_all"))

    return reminders_buttons_make_tags(
        tag_filter_is_click=tag_filter_is_click,
        keyboard=keyboard,
        tags=tags
    )


def reminders_buttons_make_tags(tag_filter_is_click: bool, keyboard: InlineKeyboardBuilder, tags):
    if tag_filter_is_click:
        if tags:
            keyboard.row(InlineKeyboardButton(text="<-", callback_data=f"reminder_tag_filter_back"))
        else:
            keyboard.row(InlineKeyboardButton(text="Вы не добавили теги, добавить?", callback_data=f"tag_new"))

        if tags:
            for tag in tags:
                keyboard.add(InlineKeyboardButton(text=tags[tag]["emoji"],
                                                  callback_data=f"reminder_tag_filter_{tags[tag]["emoji"]}"))
    else:
        keyboard.row(InlineKeyboardButton(text="Фильтрация по тэгам", callback_data="reminder_tag_filter"))

    return keyboard.as_markup()


def add_reminder_check():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Да, добавить", callback_data="reminder_check_OK"))
    keyboard.add(InlineKeyboardButton(text="Нет, ввести вручную", callback_data="reminder_check_MANUAL"))
    keyboard.add(InlineKeyboardButton(text="Отменить", callback_data="reminder_check_CANCEL"))

    return keyboard.as_markup()


def tag_menu_get_tags(tags: Sequence[dict]):
    keyboard = InlineKeyboardBuilder()

    # tag_uuid: {...: ..., ...: ...}
    for i, tag in enumerate(tags):  # for tag in tags.keys()
        keyboard.add(InlineKeyboardButton(text=str(i + 1), callback_data=f"tag_edit_id_{str(tag)}"))
    if len(tags) < get_settings().TAGS_MAX_LENGTH:
        keyboard.row(InlineKeyboardButton(text='Добавить новый тэг', callback_data=f"tag_new"))

    return keyboard.as_markup()


def tag_edit_menu_get_actions():
    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text="Имя", callback_data=f"tag_edit_action_NAME"))
    keyboard.add(InlineKeyboardButton(text='Эмодзи', callback_data=f"tag_edit_action_EMOJI"))

    return keyboard.as_markup()


def get_tag_review_buttons():
    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text="Да, добавить", callback_data=f"new_tag_process_True"))
    keyboard.add(InlineKeyboardButton(text="Отменить", callback_data=f"new_tag_process_False"))

    return keyboard.as_markup()
