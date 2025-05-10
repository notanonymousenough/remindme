from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def timezones_keyboard():
    keyboard = InlineKeyboardBuilder()

    timezones = []
    for _ in range(7):
        keyboard.add(InlineKeyboardButton(text="Поменять дату", callback_data="start_timezone_"))
        keyboard.add(InlineKeyboardButton(text="Изменить время", callback_data="start_timezone_"))

    keyboard.row(InlineKeyboardButton(text="Другое..", callback_data=f"start_timezone_another_"))

    return keyboard.as_markup()
