from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from backend.bot.keyboards import reply_kbs
from backend.bot.routers.habit_state_actions import habit_add_process_end, habit_add_process_start, \
    habit_add_process_1
from backend.bot.routers.habit_state_actions.habit_edit import habit_edit_name_0, habit_edit_name_end
from backend.bot.routers.habit_state_actions.habits_get import habits_get
from backend.bot.utils.parse_markdown_text import parse_for_markdown
from backend.bot.utils.states import States

habits_router = Router()


@habits_router.message(StateFilter(States.habits_menu),
                       F.text == "Назад")
async def return_to_menu(message: Message, state: FSMContext):
    await state.set_state(States.start_menu)

    text = "Перемещаемся в главное меню.."

    await message.answer(text=parse_for_markdown(text),
                         reply_markup=reply_kbs.main_menu(),
                         parse_mode="MarkdownV2")


@habits_router.message(StateFilter(States.habits_menu))
async def route_habit_message(message: Message, state: FSMContext):
    data = await state.get_data()
    action = data['action']

    if message.text == "Назад":
        await return_to_menu(message, state)
    elif message.text == "Добавить привычку":
        await habit_add_process_start(message, state)
    elif action == "habit_edit_rename":
        await habit_edit_name_end(message, state)
    elif action == "add_habit_process_1":
        await habit_add_process_1(message, state)
    elif action == "add_habit_process_end":
        await habit_add_process_end(message, state)
    elif not action:
        await habits_get(message, state)


@habits_router.callback_query(StateFilter(States.habits_menu),
                              F.data.startswith("habits_return_"))
async def habits_return_to_menu(call: CallbackQuery,
                                state: FSMContext):
    await return_to_menu(call.message, state)
