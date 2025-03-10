from aiogram.fsm.state import StatesGroup, State


class States(StatesGroup):
    start_menu = State()
    reminder_menu = State()
