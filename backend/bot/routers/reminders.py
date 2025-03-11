from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message

from backend.bot.keyboards import inline_kbs, reply_kbs
from backend.bot.utils.states import States

reminders_router = Router()


@reminders_router.callback_query(StateFilter(States.reminder_menu), F.data.startswith("reminder_next_"))
async def menu_next(call: CallbackData, state: FSMContext):
    next_count = int(call.dict()["data"].split("_")[-1])
    temp = "Ваши привычки: \n\n3) Отжимания (6/30) ❌\n4) Кормить кота (7/30) ✅"
    await call.message.answer(text=temp, reply_markup=inline_kbs.reminders_buttons(20, "today", next_count))


@reminders_router.callback_query(StateFilter(States.reminder_menu))
async def show_reminder(call: CallbackData, state: FSMContext):
    pass


@reminders_router.message(StateFilter(States.reminder_menu), F.text == "Фильтрация по тэгам")
async def reminder_tags(message: Message, state: FSMContext):
    await message.answer(text="134134")


@reminders_router.message(StateFilter(States.reminder_menu), F.text == "Добавить напоминание")
async def add_reminder(message: Message, state: FSMContext):
    pass


@reminders_router.message(StateFilter(States.reminder_menu), F.text == "Назад")
async def return_to_menu(message: Message, state: FSMContext):
    await state.set_state(States.start_menu)

    await message.answer(text="return to menu", reply_markup=reply_kbs.main_menu())
