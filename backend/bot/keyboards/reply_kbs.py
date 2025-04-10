from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


REMINDERS_MENU_TEXTS = ['Добавить напоминание', "Редактировать тэги", 'Назад']


def main_menu():
    menu = [
        [KeyboardButton(text="Прогресс")],
        [KeyboardButton(text="Напоминания"), KeyboardButton(text="Привычки")]
    ]
    return ReplyKeyboardMarkup(keyboard=menu, resize_keyboard=True)


def reminders_menu():
    menu = [
        [KeyboardButton(text=text_message)] for text_message in REMINDERS_MENU_TEXTS
    ]
    return ReplyKeyboardMarkup(keyboard=menu, resize_keyboard=True)


def habits_menu():
    menu = [
        [KeyboardButton(text="Добавить привычку")],
        [KeyboardButton(text="Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=menu, resize_keyboard=True)


def progress_bar():
    menu = [
        [KeyboardButton(text="Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=menu, resize_keyboard=True)
