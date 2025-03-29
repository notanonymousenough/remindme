from typing import List

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from backend.utils.habit_tools import get_last_record_status_bool
from backend.control_plane.schemas.habit import HabitSchemaResponse


def get_habit_edit_buttons(habit: HabitSchemaResponse):
    keyboard = InlineKeyboardBuilder()

    if get_last_record_status_bool(habit=habit):
        keyboard.row(InlineKeyboardButton(text="Отменить выполнение", callback_data=f"habit_complete_False_{habit.id}"))
    else:
        keyboard.row(InlineKeyboardButton(text="Выполнить", callback_data=f"habit_complete_True_{habit.id}"))
    keyboard.row(InlineKeyboardButton(text="Переименовать", callback_data=f"habit_edit_name_{habit.id}"))
    keyboard.row(InlineKeyboardButton(text="<–", callback_data=f"habit_edit_return_"))
    keyboard.add(InlineKeyboardButton(text="Удалить", callback_data=f"habit_delete_{habit.id}"))

    return keyboard.as_markup()


def habit_delete_check(habit_id):
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text="Да, удаляем", callback_data=f"habit_delete_true_{habit_id}"))
    keyboard.add(InlineKeyboardButton(text="Оставь да", callback_data=f"habit_delete_false_"))

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

    if not habits:
        keyboard.row(InlineKeyboardButton(text="Добавить первую привычку", callback_data="habits_add"))
    keyboard.row(InlineKeyboardButton(text="Назад", callback_data="habits_return_"))
    return keyboard.as_markup()
