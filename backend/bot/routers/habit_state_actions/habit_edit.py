from typing import Annotated

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from backend.bot import bot
from backend.bot.clients import get_client_async
from backend.bot.clients.remindme_api import RemindMeApiClient
from backend.bot.keyboards import inline_kbs
from backend.bot.utils import message_text_tools
from backend.bot.utils.depends import Depends
from backend.bot.utils.parse_markdown_text import parse_for_markdown
from backend.bot.utils.states import States
from backend.control_plane.routes.habit import habits_get

habit_edit_router = Router()


@habit_edit_router.callback_query(StateFilter(States.habits_menu),
                              F.data.startswith("habit_edit_return_"))
async def habit_edit(call: CallbackQuery,
                     state: FSMContext,
                     client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    await habits_get(call.message, state, need_reply=False, edit_call=True)


@habit_edit_router.callback_query(StateFilter(States.habits_menu),
                              F.data.startswith("habit_edit_"))
async def habit_edit(call: CallbackQuery,
                     state: FSMContext,
                     client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    habit_id = call.dict()["data"].split("_")[-1]
    habit = await client().habit_get(habit_id=habit_id)

    await state.update_data(habit_name=habit.text)

    text = message_text_tools.get_habit(habit)
    keyboard = inline_kbs.get_habit_edit_buttons(habit)

    await call.message.edit_text(text=parse_for_markdown(text), reply_markup=keyboard, parse_mode="MarkdownV2")
    await bot.answer_callback_query(call.id)


@habit_edit_router.callback_query(StateFilter(States.habits_menu),
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
