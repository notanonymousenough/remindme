from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu():
    menu = [
        [KeyboardButton(text="Напоминания")],
        [KeyboardButton(text="Привычки", callback_data="habits_menu")],
        [KeyboardButton(text="Прогресс", callback_data="progressbar")],
        [KeyboardButton(text="Тэги", callback_data="tags_menu")]
    ]
    return ReplyKeyboardMarkup(keyboard=menu)


def reminders_menu():
    menu = [
        [KeyboardButton(text="Добавить напоминание", callback_data="reminder_add")],
        [KeyboardButton(text="Фильтрация по тэгам", callback_data="filters")],
        [KeyboardButton(text="Назад", callback_data="main_menu")]
    ]
    return ReplyKeyboardMarkup(keyboard=menu)


def habits_menu():
    menu = [
        [KeyboardButton(text="Добавить привычку", callback_data="habit_add")],
        [KeyboardButton(text="Назад", callback_data="main_menu")]
    ]
    return ReplyKeyboardMarkup(keyboard=menu)


def progress_bar():
    menu = [
        [KeyboardButton(text="Назад", callback_data="main_menu")]
    ]
    return ReplyKeyboardMarkup(keyboard=menu)
