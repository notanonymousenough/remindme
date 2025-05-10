from typing import Annotated

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

import backend.bot.keyboards.tags_inline_kbs
from backend.bot.clients import get_client_async
from backend.bot.clients.remindme_api import RemindMeApiClient
from backend.bot.keyboards import inline_kbs
from backend.bot.utils import message_text_tools
from backend.bot.utils.depends import Depends
from backend.bot.utils.message_checkers import emoji_check
from backend.bot.utils.states import States
from backend.control_plane.schemas.requests.tag import TagRequestSchema


async def tags_edit(message: Message,
                    state: FSMContext,
                    client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    data = await state.get_data()

    access_token = data["access_token"]

    tags = await client().tags_get(access_token=access_token)

    text = message_text_tools.get_tags(tags=tags)
    markup = backend.bot.keyboards.tags_inline_kbs.tag_menu_get_tags(tags=tags)

    await message.reply(text=text, reply_markup=markup)


edit_tag_router = Router()


@edit_tag_router.callback_query(StateFilter(States.reminder_menu),
                                F.data.startswith("tag_edit_id_"))
async def tag_edit_process_0(call: CallbackQuery,
                             state: FSMContext,
                             client=Annotated[
                                 RemindMeApiClient, Depends(get_client_async)]):
    data = await state.get_data()

    tag_id = call.dict()["data"].split("_")[-1]
    await state.update_data(tag_edit_process_ID=tag_id)

    try:
        tag = await client().tag_get(tag_id=tag_id)
        text = f"Эмодзи тэга: {tag.emoji}\nИмя тэга: {tag.name}\n\nЧто вы хотите поменять?"

        keyboard = backend.bot.keyboards.tags_inline_kbs.tag_edit_menu_get_actions()
        await state.update_data(tag_edit_process_name=tag.name)
        await state.update_data(tag_edit_process_emoji=tag.emoji)

        await call.message.edit_text(text=text,
                                     parse_mode="MarkdownV2",
                                     reply_markup=keyboard)

    except Exception as ex:
        print(f"Ошибка при получении тега:  {str(ex)}")


@edit_tag_router.callback_query(StateFilter(States.reminder_menu),
                                F.data.startswith("tag_edit_action_"))
async def tag_edit_process_1(call: CallbackQuery,
                             state: FSMContext):
    data = await state.get_data()

    tag_edit_action = call.dict()["data"].split('_')[-1]
    await state.update_data(tag_edit_process_action=tag_edit_action)
    text = "None"
    if tag_edit_action == "NAME":
        text = f"Введите новое имя для тэга для тэга {data["tag_edit_process_emoji"]}"
    elif tag_edit_action == "EMOJI":
        text = f"Пришлите новое эмодзи для тэга {data["tag_edit_process_name"]}"

    await state.update_data(action="tag_edit_process_2")
    await call.message.edit_text(text=text)


@edit_tag_router.message(StateFilter(States.reminder_menu))
async def tag_edit_process_2(message: Message,
                             state: FSMContext,
                             client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    data = await state.get_data()
    tag_name, tag_emoji = None, None
    text = "None"
    try:
        if data["tag_edit_process_action"] == "NAME":
            tag_name = message.text
            tag_emoji = data["tag_edit_process_emoji"]
        elif data["tag_edit_process_action"] == "EMOJI":
            tag_emoji = emoji_check(message.text)
            tag_name = data["tag_edit_process_name"]

        if tag_emoji:
            request = {
                "name": tag_name,
                "emoji": tag_emoji
            }
            tag_id = data['tag_edit_process_ID']
            request = TagRequestSchema.model_validate(request)

            if await client().tag_put(request=request, tag_id=tag_id):
                text = "Тэг успешно обновлен."
                await state.update_data(action=None)
                await message.reply(text=text)
                await tags_edit(message=message, state=state)
                return
        else:
            text = "Это не эмодзи, попробуй еще раз"

    except Exception as ex:
        text = "Ошибка при отправке на сервер"
        print(f"Ошибка при отправке на сервер: {ex}")

    await message.reply(text=text)
