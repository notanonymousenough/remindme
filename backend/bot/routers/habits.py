from typing import Annotated

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from backend.bot import bot
from backend.bot.clients import get_client_async
from backend.bot.clients.remindme_api import RemindMeApiClient
from backend.bot.keyboards import inline_kbs, reply_kbs
from backend.bot.routers.habit_state_actions import habit_add_process_end, habit_add_process_start, \
    habit_add_process_1
from backend.bot.utils import message_text_tools, habit_tools
from backend.bot.utils.depends import Depends
from backend.bot.utils.parse_markdown_text import parse_for_markdown
from backend.bot.utils.states import States

habits_router = Router()


@habits_router.message(StateFilter(States.habits_menu))
async def route_habit_message(message: Message, state: FSMContext):
    data = await state.get_data()
    action = data['action']

    if message.text == "Назад":
        await return_to_menu(message, state)

    elif message.text == "Добавить привычку":
        await habit_add_process_start(message, state)
    elif action == "add_habit_process_1":
        await habit_add_process_1(message, state)
    elif action == "add_habit_process_end":
        await habit_add_process_end(message, state)

    elif not action:
        await habits_get(message, state)


@habits_router.message(StateFilter(States.habits_menu),
                       F.text == "Назад")
async def return_to_menu(message: Message, state: FSMContext):
    await state.set_state(States.start_menu)

    text = "Перемещаемся в главное меню.."

    await message.answer(text=parse_for_markdown(text),
                         reply_markup=reply_kbs.main_menu(),
                         parse_mode="MarkdownV2")


@habits_router.callback_query(StateFilter(States.habits_menu),
                              F.data.startswith("habit_edit_"))
async def habit_edit(call: CallbackQuery,
                     state: FSMContext,
                     client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    data = await state.get_data()
    habit_id = call.dict()["data"].split("_")[-1]
    habit = await client().habit_get(habit_id=habit_id)
    text = message_text_tools.get_habit(habit)

    keyboard = inline_kbs.get_habit_edit_buttons(habit)

    await call.message.answer(text=parse_for_markdown(text), reply_markup=keyboard, parse_mode="MarkdownV2")
    await bot.answer_callback_query(call.id)


@habits_router.callback_query(StateFilter(States.habits_menu),
                              F.data.startswith("habit_complete_"))
async def habit_change_status(call: CallbackQuery,
                              state: FSMContext,
                              client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    data = await state.get_data()
    action = call.dict()["data"].split("_")[-2]
    access_token = data["access_token"]
    habit_id = call.dict()["data"].split("_")[-1]
    if action == "True":
        await client().habit_progress_post(access_token=access_token, habit_id=habit_id)
    elif action == "False":
        await client().habit_progress_delete_last(habit_id=habit_id)
    await habit_edit(call, state)


async def habits_get(message: Message,
                     state: FSMContext,
                     client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    data = await state.get_data()

    next_coef = data["next_coef"]
    habits = sorted((await client().habits_get(state_data=data)), key=lambda x: x.updated_at)
    text = message_text_tools.get_habits(habits=habits)

    await message.answer(text="Вывожу список привычек..", reply_markup=reply_kbs.habits_menu())
    await message.answer(text=parse_for_markdown(text),
                         reply_markup=inline_kbs.get_habits_buttons(habits=habits, next_coef=next_coef),
                         parse_mode="MarkdownV2")
