from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from backend.bot.clients.remindme_api import RemindMeApiClient


def reminders_buttons(data: dict):
    next_coef = data["next_coef"]
    reminders = data["reminders"]

    keyboard = InlineKeyboardBuilder()

    count_of_reminders = len(reminders)
    increase = 5*next_coef

    start_index = increase
    end_index = min(start_index + 5, count_of_reminders)

    if start_index > 1:
        keyboard.row(InlineKeyboardButton(text="<-", callback_data=f"reminder_previous_{next_coef - 1}"))

    for index in range(start_index, end_index):
        reminder_id = reminders[index]['id']
        keyboard.row(InlineKeyboardButton(text=str(index+1), callback_data=f"reminder_{reminder_id}_today"))

    if end_index < count_of_reminders:
        keyboard.row(InlineKeyboardButton(text="->", callback_data=f"reminder_next_{next_coef + 1}"))

    keyboard.adjust(7)

    days = {
        "today": "reminder_filter_today",
        "tomorrow": "reminder_filter_tomorrow",
        "all": "reminder_filter_others"
    }

    keyboard.row(InlineKeyboardButton(text="Сегодня", callback_data=days["today"]))
    keyboard.add(InlineKeyboardButton(text="Завтра", callback_data=days["tomorrow"]))
    keyboard.add(InlineKeyboardButton(text="ВСЕ", callback_data=days["all"]))

    return keyboard.as_markup()
