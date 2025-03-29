from typing import Annotated

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from backend.bot.clients import get_client_async
from backend.bot.clients.remindme_api import RemindMeApiClient
from backend.bot.keyboards import tags_inline_kbs
from backend.bot.utils import message_text_tools
from backend.bot.utils.depends import Depends
from backend.bot.utils.parse_markdown_text import parse_for_markdown


async def tags_get(message: Message,
                   state: FSMContext,
                   client=Annotated[RemindMeApiClient, Depends(get_client_async)],
                   text: str = ""):
    data = await state.get_data()

    access_token = data["access_token"]

    tags = await client().tags_get(access_token=access_token)

    text += message_text_tools.get_tags(tags=tags)
    markup = tags_inline_kbs.tag_menu_get_tags(tags=tags)

    await message.reply(text=parse_for_markdown(text), reply_markup=markup, parse_mode="MarkdownV2")
