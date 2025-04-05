from typing import Annotated, Union

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from aiogram.types import Message, CallbackQuery

from backend.bot import bot
from backend.bot.clients import get_client_async
from backend.bot.clients.remindme_api import RemindMeApiClient

from backend.bot.keyboards import inline_kbs, reply_kbs

from backend.bot.utils import message_text_tools
from backend.bot.utils.depends import Depends
from backend.bot.utils.message_checkers import emoji_check
from backend.bot.utils.state_data_tools import state_data_reset
from backend.bot.utils.states import States

reminders_router = Router()

from aiogram import Router

tags_router = Router()
"""
По сути разделение роутеров –
это лишь условность для чистого кода.
State остается таким, как в reminder_route
"""


async def _tags(message_or_call: Union[CallbackQuery, Message],
                state: FSMContext,
                client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    data = await state.get_data()

    tags = await client().get_tags(state_data=data)
    if tags:
        text = message_text_tools.get_tags_edit(tags=tags)
    else:
        text = "Какое эмодзи будет у вашего тэга?"
        await state.update_data(new_tag_review=True)

    await bot.send_message(chat_id=message_or_call.chat.id,
                           text=text,
                           reply_markup=inline_kbs.tag_menu_get_tags(tags=tags) if tags else None,
                           parse_mode="MarkdownV2")


@tags_router.message(StateFilter(States.reminder_menu))
async def new_tag_process_1(message: Message,
                           state: FSMContext):
    data = await state.get_data()
    if not data["new_tag_review"]:
        return
    if not emoji_check(message.text):
        text = "Пожалуйста, пришлите эмодзи!"
        await message.edit_text(text=text)

    await state.update_data(new_tag_emoji=message.text)

    text = "А теперь придумайте имя тэга, который ассоциируется с этим эмодзи"

    await message.edit_text(text=text)


@tags_router.message(StateFilter(States.reminder_menu))
async def new_tag_process_2(message: Message,
                           state: FSMContext):

    data = await state.get_data()
    if not data["new_tag_review"]:
        return

    text = f"{data["new_tag_emoji"]} – {message.text}. \n\nВсе верно?"

    await message.edit_text(text=text, reply_markup=inline_kbs.get_tag_review_buttons())


@tags_router.message(StateFilter(States.reminder_menu),
                     F.data.startswith("new_tag_process_"))
async def new_tag_process_3(call: CallbackQuery,
                           state: FSMContext):
    answer = call.message.text.split("_")[-1]

    data = await state.get_data()
    if bool(answer):
        text=f"Тэг {data["new_tag_emoji"]} успешно добавлен!"

    text = "Создание тэга отменено"
    await state_data_reset(state=state, telegram_id=call.from_user.id)

    await call.answer(text=text)


@tags_router.callback_query(StateFilter(States.reminder_menu),
                            F.data.startswith("tag_edit_"))
async def tag_edit_(call: CallbackQuery, state: FSMContext):  # TODO(Arsen): edit tag by tag_id
    data = await state.get_data()

    tag_id_to_edit = call.message.text.split("_")[-1]

    text = "Эмодзи тэга: {}\nИмя тэга: {}\n\nЧто вы хотите поменять?"

    keyboard = None  # TODO

    await call.message.answer(text=text,
                      parse_mode="MarkdownV2",
                      reply_markup=keyboard)
