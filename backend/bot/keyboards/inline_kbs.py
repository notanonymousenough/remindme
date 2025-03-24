from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from backend.bot.clients import client


def get_habits_buttons(habits):
    keyboard = InlineKeyboardBuilder()

    habits_count = len(habits)

    for index in range(habits_count):
        habit_id = habits[index]["habit_id"]
        keyboard.add(InlineKeyboardButton(text=str(index + 1), callback_data=f"habit_edit_{habit_id}"))

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

    days = {
        "today": "reminder_day_filter_today",
        "tomorrow": "reminder_day_filter_tomorrow",
        "all": "reminder_day_filter_all"
    }

    keyboard.row(InlineKeyboardButton(text=f"✅ Сегодня" if day_filter == "today" else "Сегодня",
                                      callback_data=days["today"]))
    keyboard.add(InlineKeyboardButton(text="✅ Завтра" if day_filter == "tomorrow" else "Завтра",
                                      callback_data=days["tomorrow"]))
    keyboard.add(InlineKeyboardButton(text="✅ ВСЕ" if day_filter == "all" else "Остальные дни",
                                      callback_data=days["all"]))

    return reminders_buttons_make_tags(
        tag_filter_is_click = tag_filter_is_click,
        keyboard=keyboard,
        tags=tags
    )


def reminders_buttons_make_tags(tag_filter_is_click: bool, keyboard: InlineKeyboardBuilder, tags):
    if tag_filter_is_click:
        keyboard.row(InlineKeyboardButton(text="<-", callback_data=f"reminder_tag_filter_back"))

        for tag in tags:
            keyboard.add(InlineKeyboardButton(text=tags[tag]["emoji"], callback_data=f"reminder_tag_filter_{tags[tag]["emoji"]}"))
    else:
        keyboard.row(InlineKeyboardButton(text="Фильтрация по тэгам", callback_data="reminder_tag_filter"))

    return keyboard.as_markup()


def add_reminder_check():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Да, добавить", callback_data="reminder_check_OK"))
    keyboard.add(InlineKeyboardButton(text="Отменить", callback_data="reminder_check_CANCEL"))

    return keyboard.as_markup()


def tag_menu_get_tags(tags):
    keyboard = InlineKeyboardBuilder()

    for i, tag in enumerate(tags):
        keyboard.add(InlineKeyboardButton(text=str(i + 1), callback_data=f"tags_edit_{str(tag)}"))

    return keyboard.as_markup()
