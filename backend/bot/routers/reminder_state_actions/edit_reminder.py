from typing import Annotated, Union
from uuid import UUID

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from backend.bot import bot
from backend.bot.clients import get_client_async
from backend.bot.clients.remindme_api import RemindMeApiClient
from backend.bot.keyboards import inline_kbs
from backend.bot.utils import States, message_text_tools
from backend.bot.utils.depends import Depends
from backend.bot.utils.parse_markdown_text import parse_for_markdown
from backend.control_plane.schemas.requests.reminder import ReminderEditNameRequest

edit_reminder_router = Router(name="edit_reminder_router")


@edit_reminder_router.callback_query(StateFilter(States.reminder_menu),
                                     F.data.startswith("reminder_edit_complete_"))
async def reminder_edit_complete(call: CallbackQuery,
                                 state: FSMContext,
                                 client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    data = await state.get_data()
    access_token = data['access_token']

    modes = data['mode']
    new_mode = [call.model_dump()['data'].split("_")[-2]]
    await state.update_data(mode=data['mode'] + new_mode)
    modes = new_mode + modes

    tags = [None]
    if "tag" in modes:
        tags = await client().tags_get(access_token=access_token)

    reminder_id = call.model_dump()['data'].split("_")[-1]
    reminder = await client().reminder_get(access_token, reminder_id)

    # complete reminder
    await client().reminder_complete(access_token=access_token, reminder_id=reminder_id, status=reminder.status)
    reminder = await client().reminder_get(access_token=access_token, reminder_id=reminder_id)

    text = message_text_tools.get_reminder(reminder)
    keyboard = inline_kbs.edit_reminder(reminder, modes=modes, tags=tags)

    await call.message.edit_text(text=parse_for_markdown(text), reply_markup=keyboard, parse_mode="MarkdownV2")
    await bot.answer_callback_query(call.id)


@edit_reminder_router.callback_query(StateFilter(States.reminder_menu),
                                     F.data.startswith("reminder_edit_rename_"))
async def reminder_edit_name(call: CallbackQuery,
                             state: FSMContext,
                             client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    await state.update_data(action="reminder_edit_name")

    text = "Какое будет имя у напоминания?"

    await call.message.edit_text(text=parse_for_markdown(text), parse_mode="MarkdownV2")
    await bot.answer_callback_query(call.id)


@edit_reminder_router.message(StateFilter(States.reminder_menu))
async def reminder_edit_name_check(message: Message,
                                   state: FSMContext,
                                   client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    data = await state.get_data()
    access_token = data["access_token"]
    reminder_id = data["reminder_edit_id"]
    reminder_name = message.text

    request = ReminderEditNameRequest.model_validate(
        {
            "id": reminder_id,
            "text": reminder_name
        }
    )

    if await client().reminder_put(access_token=access_token, request=request):
        await _reminder_edit(message, state, text="Напоминание переименовано. \n\n")
    else:
        await _reminder_edit(message, state, text="Ошибка отправки на сервер..\n\n")


@edit_reminder_router.callback_query(StateFilter(States.reminder_menu),
                                     F.data.startswith("reminder_edit_tag_change_"))
async def reminder_edit_tag(call: CallbackQuery,
                            state: FSMContext,
                            client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    data = await state.get_data()
    access_token = data['access_token']

    mode = data['mode']
    new_mode = [call.model_dump()['data'].split("_")[-2]]
    await state.update_data(mode=data['mode'] + new_mode)
    mode = new_mode + mode

    tag_id_to_delete = None
    new_tag_id = UUID(call.model_dump()['data'].split("_")[-1])
    reminder_id = data['reminder_edit_id']

    reminder = await client().reminder_get(access_token=access_token, reminder_id=reminder_id)

    reminder_tags = []
    if reminder.tags:
        reminder_tags = [tag.id for tag in reminder.tags]
    if new_tag_id in reminder_tags:
        tag_id_to_delete = new_tag_id
        new_tag_id = None

    # TODO сделать return reminder schema (для этого сделать доп ручку в апи)
    await client().change_reminder_tags(
        access_token=access_token,
        reminder_id=reminder_id,
        tag_to_add=new_tag_id,
        tag_to_delete=tag_id_to_delete
    )
    reminder = await client().reminder_get(
        access_token=access_token,
        reminder_id=reminder_id
    )

    text = message_text_tools.get_reminder(reminder)

    tags = await client().tags_get(access_token)

    keyboard = inline_kbs.edit_reminder(reminder=reminder, tags=tags, modes=mode)

    await call.message.edit_text(text=parse_for_markdown(text), reply_markup=keyboard, parse_mode="MarkdownV2")
    await bot.answer_callback_query(call.id)


@edit_reminder_router.callback_query(StateFilter(States.reminder_menu),
                                     F.data.startswith("reminder_edit_tag_"))
async def reminder_edit_tag(call: CallbackQuery,
                            state: FSMContext,
                            client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    data = await state.get_data()
    access_token = data['access_token']

    mode = data['mode']
    new_mode = [call.model_dump()['data'].split("_")[-2]]
    await state.update_data(mode=data['mode'] + new_mode)
    mode = new_mode + mode

    reminder_id = data['reminder_edit_id']
    reminder = await client().reminder_get(access_token=access_token, reminder_id=reminder_id)

    tags = await client().tags_get(access_token=access_token)

    keyboard = inline_kbs.edit_reminder(reminder, mode, tags)

    await call.message.edit_reply_markup(reply_markup=keyboard, parse_mode="MarkdownV2")
    await bot.answer_callback_query(call.id)


@edit_reminder_router.callback_query(StateFilter(States.reminder_menu),
                                     F.data.startswith("reminder_edit_"))
async def reminder_edit(call: CallbackQuery,
                        state: FSMContext,
                        client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    await _reminder_edit(call, state, client)


async def _reminder_edit(message: Union[Message, CallbackQuery],
                         state: FSMContext,
                         client=Annotated[RemindMeApiClient, Depends(get_client_async)],
                         text: str = ""):
    data = await state.get_data()
    access_token = data['access_token']

    if type(message) == CallbackQuery:
        reminder_id = message.model_dump()['data'].split("_")[-1]
    else:
        reminder_id = data["reminder_edit_id"]

    async def reset_mode_state():
        new_mode = ['edit']
        await state.update_data(
            {
                "action": "reminder_edit",
                "modes": new_mode,
                "reminder_edit_id": reminder_id
            }
        )
        return new_mode

    mode = await reset_mode_state()

    reminder = await client().reminder_get(access_token=access_token, reminder_id=reminder_id)

    text = f"*{text}*" + message_text_tools.get_reminder(reminder)

    keyboard = inline_kbs.edit_reminder(reminder, modes=mode)

    if type(message) == CallbackQuery:
        await message.message.edit_text(text=parse_for_markdown(text), reply_markup=keyboard, parse_mode="MarkdownV2")
        await bot.answer_callback_query(message.id)
    else:
        await message.answer(text=parse_for_markdown(text), reply_markup=keyboard, parse_mode="MarkdownV2")
