from typing import Annotated, Union

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from backend.bot import bot
from backend.bot.clients import get_client_async
from backend.bot.clients.remindme_api import RemindMeApiClient
from backend.bot.keyboards import inline_kbs
from backend.bot.routers.tag_state_actions.edit_tag import tags_edit
from backend.bot.utils.depends import Depends
from backend.bot.utils.message_checkers import emoji_check
from backend.bot.utils.state_data_tools import state_data_reset
from backend.bot.utils.states import States
from backend.control_plane.schemas.requests.tag import TagRequestSchema

new_tag_router = Router()


@new_tag_router.callback_query(StateFilter(States.reminder_menu),
                               F.data.startswith("tag_new"))
async def new_tag_process_from_callback(call: CallbackQuery,
                                        state: FSMContext,
                                        client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    await new_tag_process_0(call, state, client)


async def tags_edit_no_tags(message: Message,  # КОГДА НЕТ ТЭГОВ
                            state: FSMContext,
                            client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    data = await state.get_data()
    tags = await client().tags_get(state_data=data)
    if not tags:
        await new_tag_process_0(message, state)


async def new_tag_process_0(message_or_call: Union[CallbackQuery, Message],
                            state: FSMContext,
                            client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    data = await state.get_data()
    tags = await client().tags_get(state_data=data)
    await state.update_data(action="new_tag_process_1")

    if tags:
        text = "Какое эмодзи будет у нового тэга?"
    else:
        text = "Какое эмодзи будет у вашего первого тэга?"

    if type(message_or_call) is Message:
        await message_or_call.edit_text(text=text, parse_mode="MarkdownV2")
    elif type(message_or_call) is CallbackQuery:
        await message_or_call.message.edit_text(text=text, parse_mode="MarkdownV2")
        await bot.answer_callback_query(message_or_call.id)
    return None


@new_tag_router.message(StateFilter(States.reminder_menu))
async def new_tag_process_1(message: Message,
                            state: FSMContext):
    if not emoji_check(message.text):
        text = "Пожалуйста, пришлите эмодзи!"
    else:
        await state.update_data(action="new_tag_process_2")
        await state.update_data(new_tag_emoji=message.text)
        text = "А теперь придумайте имя тэга, который ассоциируется с этим эмодзи"

    await message.reply(text=text)


@new_tag_router.message(StateFilter(States.reminder_menu))
async def new_tag_process_2(message: Message,
                            state: FSMContext):
    data = await state.get_data()
    await state.update_data(new_tag_name=message.text)
    text = f"{data["new_tag_emoji"]} – {message.text}. \n\nВсе верно?"

    await message.reply(text=text, reply_markup=inline_kbs.get_tag_review_buttons())


@new_tag_router.callback_query(StateFilter(States.reminder_menu),
                               F.data.startswith("new_tag_process_"))
async def new_tag_process_3_call(call: CallbackQuery,
                                 state: FSMContext,
                                 client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    answer = call.dict()['data'].split("_")[-1]

    data = await state.get_data()
    if answer == "True":
        try:
            tag_name = data['new_tag_name']
            tag_emoji = data['new_tag_emoji']
            request = {
                'name': tag_name,
                'emoji': tag_emoji
            }
            request = TagRequestSchema.model_validate(request)
            await client().tag_post(data["access_token"], request=request)

            text = f"Тэг {tag_emoji} {tag_name} успешно добавлен!"

        except Exception as ex:
            text = f"Ошибка при отправке на сервер: {ex}"
    else:
        text = "Создание тэга отменено"

    await state_data_reset(state=state, telegram_id=call.from_user.id, access_token=data['access_token'])
    await call.message.edit_text(text=text)

    await tags_edit(message=call.message, state=state)
