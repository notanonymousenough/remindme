from typing import Annotated
from uuid import UUID

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from backend.bot import bot
from backend.bot.clients import get_client_async
from backend.bot.clients.remindme_api import RemindMeApiClient
from backend.bot.keyboards import inline_kbs
from backend.bot.utils import States, message_text_tools, date_formatting
from backend.bot.utils.depends import Depends
from backend.bot.utils.parse_markdown_text import parse_for_markdown
from backend.control_plane.schemas.requests.reminder import ReminderToEditTimeRequestSchema, ReminderChangeTagsRequest

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
                                     F.data.startswith("reminder_edit_datetime_time"))
async def reminder_edit_datetime_time(call: CallbackQuery,
                                      state: FSMContext,
                                      client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    text = "Введи новое время, например 14:00 или 2 часа дня"

    await call.message.edit_text(text=text)
    await bot.answer_callback_query(call.id)


@edit_reminder_router.message(StateFilter(States.reminder_menu))
async def reminder_edit_datetime_time_check(message: Message,
                                            state: FSMContext,
                                            client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    data = await state.get_data()
    access_token = data["access_token"]

    try:
        reminder_time = date_formatting.get_correct_time(message.text)
        request = ReminderToEditTimeRequestSchema.model_validate(
            {
                "id": data["reminder_id"],
                "time": reminder_time,
            }
        )
        await client().reminder_postpone(access_token=access_token, request=request)
        text = "Время напоминания обновлено!"
    except:
        text = "Неверный формат времени"

    await message.answer(text=text)


@edit_reminder_router.callback_query(StateFilter(States.reminder_menu),
                                     F.data.startswith("reminder_edit_datetime_"))
async def reminder_edit_datetime_(call: CallbackQuery,
                                  state: FSMContext,
                                  client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    data = await state.get_data()
    access_token = data['access_token']

    reminder_id = call.model_dump()['data'].split("_")[-1]

    reminder = await client().reminder_get(access_token=access_token, reminder_id=reminder_id)

    keyboard = inline_kbs.edit_reminder(reminder, ["datetime"])  # one mode only
    await call.message.edit_reply_markup(reply_markup=keyboard)
    await bot.answer_callback_query(call.id)


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
    data = await state.get_data()
    access_token = data['access_token']

    async def reset_mode_state():
        new_mode = ['edit']
        await state.update_data(modes=new_mode)
        return new_mode

    mode = await reset_mode_state()

    reminder_id = call.model_dump()['data'].split("_")[-1]
    await state.update_data(reminder_edit_id=reminder_id)  # set reminder_id in state data

    reminder = await client().reminder_get(access_token=access_token, reminder_id=reminder_id)

    text = message_text_tools.get_reminder(reminder)
    keyboard = inline_kbs.edit_reminder(reminder, modes=mode)

    await call.message.edit_text(text=parse_for_markdown(text), reply_markup=keyboard, parse_mode="MarkdownV2")
    await bot.answer_callback_query(call.id)
