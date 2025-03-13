from aiogram import Router, F
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from backend.bot.keyboards import reply_kbs, inline_kbs
from backend.bot.utils import States, get_message_reminders

from backend.bot.clients import client

start_router = Router()


@start_router.message(CommandStart())
async def start_menu(message: Message, state: FSMContext):
    await state.set_state(States.start_menu)
    await message.answer(text="Нажмите кнопку :)", reply_markup=reply_kbs.main_menu())


@start_router.message(F.text == "Напоминания")
async def reminders(message: Message, state: FSMContext):
    await state.set_state(States.reminder_menu)  # set state for reminders menu
    await state.set_data({
        "day": "сегодня",
        "user_id": message.from_user.id,
        "reminders": client.get_reminders(user=None, day="завтра"),  # туда потом передаем user_id
        "next_coef": 0,
        "strip": [0, 5]
    })
    data = await state.get_data()

    text = get_message_reminders(data=data)

    await message.answer(text=text,
                         reply_markup=inline_kbs.reminders_buttons(data=data),
                         parse_mode="MarkdownV2")

    await message.answer(text="..", reply_markup=reply_kbs.reminders_menu())


@start_router.message(F.text == "Привычки")
async def habits(message: Message, state: FSMContext):
    pass


@start_router.message(F.text == "")
async def progress():
    pass


@start_router.message()  #  StateFilter(States.start_menu)
async def text_from_user(message: Message, state: FSMContext):
    await start_menu(message, state)
