from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from backend.control_plane.db.models import HabitPeriod

REMINDERS_MENU_TEXTS = ['Добавить напоминание', "Редактировать тэги", 'Назад']
HABITS_ADD_PROCESS = ["Раз в день", "Раз в неделю", "Раз в месяц"]
HABITS_ADD_PROCESS_INTERVALS = {
    HABITS_ADD_PROCESS[i]: HabitPeriod
    for i, HabitPeriod in enumerate(HabitPeriod) if i < len(HABITS_ADD_PROCESS)
}


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


def habits_add_process():
    actions = [
        [KeyboardButton(text=action_text) for action_text in HABITS_ADD_PROCESS]
    ]
    return ReplyKeyboardMarkup(keyboard=actions, resize_keyboard=True)


def progress_bar():
    menu = [
        [KeyboardButton(text="Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=menu, resize_keyboard=True)
