from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu():
    menu = [
        [KeyboardButton(text="Прогресс")],
        [KeyboardButton(text="Напоминания"), KeyboardButton(text="Привычки")]
    ]
    return ReplyKeyboardMarkup(keyboard=menu)


def reminders_menu():
    menu = [
        [KeyboardButton(text="Добавить напоминание")],
        [KeyboardButton(text="Редактировать тэги")],
        [KeyboardButton(text="Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=menu)


def habits_menu():
    menu = [
        [KeyboardButton(text="Добавить привычку")],
        [KeyboardButton(text="Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=menu)


def progress_bar():
    menu = [
        [KeyboardButton(text="Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=menu)
