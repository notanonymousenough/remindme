from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from random import randint

count_of_reminders = randint(2, 10)
day = "today"


def reminders_buttons(count_of_reminders: int, day: str, next_coef = 0):
    keyboard = InlineKeyboardBuilder()

    increase = 0
    if next_coef:
        increase += 5 * next_coef

    for index, reminder_id in enumerate(range(1+increase, count_of_reminders + increase)):
        keyboard.row(InlineKeyboardButton(text=str(reminder_id), callback_data=f"reminder_{str(reminder_id)}_today"))
        if index == 4 or increase+index+1 >= count_of_reminders:
            break

    if count_of_reminders > 5*(next_coef + 1):
        keyboard.row(InlineKeyboardButton(text="->", callback_data=f"reminder_next_{next_coef + 1}"))

    keyboard.adjust(6)
    return keyboard.as_markup()
