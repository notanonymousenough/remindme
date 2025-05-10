from typing import Annotated
from uuid import UUID

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import backend.bot.keyboards.habits_inline_kbs
from backend.bot import bot
from backend.bot.clients import get_client_async
from backend.bot.clients.remindme_api import RemindMeApiClient
from backend.bot.routers.habit_state_actions.habits_get import habits_get
from backend.bot.utils import message_text_tools
from backend.bot.utils.depends import Depends
from backend.bot.utils.parse_markdown_text import parse_for_markdown
from backend.bot.utils.states import States
from backend.control_plane.schemas.requests.habit import HabitPutRequest

habit_edit_router = Router()


@habit_edit_router.callback_query(StateFilter(States.habits_menu),
                                  F.data.startswith("habit_edit_name_"))
async def habit_edit_name_0(call: CallbackQuery,
                            state: FSMContext,
                            client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    await state.update_data(action="habit_edit_rename")
    text = "Введи новое название привычки"
    await call.message.answer(text=text)


async def habit_edit_name_end(message: Message,
                              state: FSMContext,
                              client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    data = await state.get_data()

    access_token = data['access_token']
    habit_id = data['habit_id']
    new_habit_name = message.text

    request = HabitPutRequest.model_validate(
        {
            "habit_id": UUID(habit_id), "text": new_habit_name
        }
    )
    if await client().habit_put(access_token=access_token, habit_id=habit_id, request=request):
        text = "*Привычка переименована!*"
    else:
        text = "*ОШИБКА ОТПРАВКИ НА СЕРВЕР*"

    await habits_get(message, state, need_reply=False, text=text, edit_call=False)


@habit_edit_router.callback_query(StateFilter(States.habits_menu),
                                  F.data.startswith("habit_edit_return_"))
async def habit_edit_return(call: CallbackQuery,
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

    await state.update_data(
        {
            "habit_name": habit.text,
            "habit_id": habit_id
        }
    )

    text = message_text_tools.get_habit(habit)
    keyboard = backend.bot.keyboards.habits_inline_kbs.get_habit_edit_buttons(habit)

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
