from aiogram import Router, F
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from backend.bot.keyboards import reply_kbs, inline_kbs
from backend.bot.utils.States import States

start_route = Router()


@start_route.message(CommandStart())
async def start_menu(message: Message, state: FSMContext):
    await state.set_state(States.start_menu)
    await message.answer(text="Нажмите кнопку :)", reply_markup=reply_kbs.main_menu())


@start_route.message(F.text == "Напоминания")
async def reminders_select(message: Message, state: FSMContext):
    temp = "Ваши привычки: \n\n1) Отжимания (6/30) ❌\n2) Кормить кота (7/30) ✅"

    await state.set_state(States.reminder_menu)  # set state for reminders menu

    await message.answer(text=temp, reply_markup=inline_kbs.reminders_buttons(20, "today"))
    await message.answer(text="..", reply_markup=reply_kbs.reminders_menu())


@start_route.message(StateFilter(States.start_menu))
async def text_from_user(message: Message, state: FSMContext):
    await start_menu(message, state)
