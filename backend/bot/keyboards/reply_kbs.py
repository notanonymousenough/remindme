from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


MENU_MESSAGES_TEXT = ['Добавить напоминание', "Редактировать тэги", 'Назад']


def main_menu():
    menu = [
        [KeyboardButton(text="Прогресс")],
        [KeyboardButton(text="Напоминания"), KeyboardButton(text="Привычки")]
    ]
    return ReplyKeyboardMarkup(keyboard=menu)


def reminders_menu():
    menu = [
        [KeyboardButton(text=text_message)] for text_message in MENU_MESSAGES_TEXT
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
