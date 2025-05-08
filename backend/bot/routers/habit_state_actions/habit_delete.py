from typing import Annotated

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from backend.bot.clients.remindme_api import RemindMeApiClient, get_client_async
from backend.bot.keyboards import inline_kbs
from backend.bot.routers.habits import habits_get
from backend.bot.utils import States
from backend.bot.utils.depends import Depends
from backend.bot.utils.parse_markdown_text import parse_for_markdown

habit_delete_router = Router()


@habit_delete_router.callback_query(StateFilter(States.habits_menu),
                                    F.data.startswith("habit_delete_false"))
async def habit_delete_check(call: CallbackQuery,
                             state: FSMContext,
                             client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    text = "*Удаление привычки отменено!*\n\n"
    await habits_get(call.message, state, text=text, need_reply=False, edit_call=True)


@habit_delete_router.callback_query(StateFilter(States.habits_menu),
                                    F.data.startswith("habit_delete_true"))
async def habit_delete_check(call: CallbackQuery,
                             state: FSMContext,
                             client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    pass
    data = await state.get_data()
    habit_id = call.dict()["data"].split("_")[-1]

    await client().habit

    text = f"*Привычка {habit.name} удалена!*\n\n"
    await habits_get(call.message, state, text=text, need_reply=False)


@habit_delete_router.callback_query(StateFilter(States.habits_menu),
                                    F.data.startswith("habit_delete_"))
async def habit_delete_check(call: CallbackQuery,
                             state: FSMContext,
                             client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    habit_id = call.dict()['data'].split("_")[-1]

    text = "Вы точно хотите удалить эту привычку?"
    keyboard = inline_kbs.habit_delete_check(habit_id)

    await call.message.edit_text(text=parse_for_markdown(text), reply_markup=keyboard, parse_mode="MarkdownV2")
