from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from aiogram.types import Message, CallbackQuery

from backend.bot import bot
from backend.bot.keyboards import inline_kbs, reply_kbs
from backend.bot.routers import start as start_router

from backend.bot.utils.states import States

habits_router = Router()


@habits_router.message(StateFilter(States.habits_menu),
                       F.text == "Назад")
async def return_to_menu(message: Message, state: FSMContext):
    await state.set_state(States.start_menu)

    text = "Перемещаемся в главное меню\.\."


    await message.answer(text=text,
                         reply_markup=reply_kbs.main_menu(),
                         parse_mode="MarkdownV2")


@habits_router.message(StateFilter(States.habits_menu),
                       F.text == "Добавить привычку")
async def habit_add(message: Message, state: FSMContext):
    await state.update_data(habit_add=1)
    data = state.get_data()

    text = "🧩 Введите название вашей новой привычки\."

    await message.answer(text=text,
                         parse_mode="MarkdownV2")


@habits_router.callback_query(StateFilter(States.habits_menu),
                              F.data.startswith("habit_edit_"))
async def habit_edit(call: CallbackQuery, state: FSMContext):
    data = state.get_data()

    await call.message.answer(text="разработчик еще не сделал редактирование привычек)")
    await bot.answer_callback_query(call.id)


@habits_router.message(StateFilter(States.habits_menu))
async def habit_check(message: Message, state: FSMContext):
    data = await state.get_data()
    if not data["habit_add"]:
        return

    text = f"Привычка {message.text} добавлена\!"

    await message.answer(text=text,
                         parse_mode="MarkdownV2")

    await start_router.habits(message=message, state=state)
