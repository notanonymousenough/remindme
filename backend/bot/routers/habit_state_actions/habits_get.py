from typing import Annotated

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import backend.bot.keyboards.habits_inline_kbs
from backend.bot.clients import get_client_async
from backend.bot.clients.remindme_api import RemindMeApiClient
from backend.bot.keyboards import reply_kbs
from backend.bot.utils import message_text_tools
from backend.bot.utils.depends import Depends
from backend.bot.utils.parse_markdown_text import parse_for_markdown


async def habits_get(message: Message,
                     state: FSMContext,
                     client=Annotated[RemindMeApiClient, Depends(get_client_async)],
                     need_reply: bool = False,
                     text: str = "",
                     edit_call: bool = False):
    data = await state.get_data()
    access_token = data['access_token']
    next_coef = data["next_coef"]

    habits = sorted((await client().habits_get(access_token=access_token)), key=lambda x: x.updated_at)

    text += message_text_tools.get_habits(habits=habits)

    if need_reply:
        text_reply = "Вывожу список привычек.."
        await message.answer(text=text_reply, reply_markup=reply_kbs.habits_menu())

    if edit_call:
        await message.edit_text(text=parse_for_markdown(text),
                                reply_markup=backend.bot.keyboards.habits_inline_kbs.get_habits_buttons(habits=habits, next_coef=next_coef),
                                parse_mode="MarkdownV2")
    else:
        await message.answer(text=parse_for_markdown(text),
                             reply_markup=backend.bot.keyboards.habits_inline_kbs.get_habits_buttons(habits=habits, next_coef=next_coef),
                             parse_mode="MarkdownV2")