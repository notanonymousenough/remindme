from typing import Annotated

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

    mode = data['mode']
    new_mode = [call.model_dump()['data'].split("_")[-2]]
    await state.update_data(mode=data['mode']+new_mode)
    mode = new_mode + mode

    tags = [None]
    if "tag" in mode:
        tags = await client().tags_get(access_token=access_token)

    reminder_id = call.model_dump()['data'].split("_")[-1]
    reminder = await client().reminder_get(access_token, reminder_id)

    # complete reminder
    await client().reminder_complete(access_token=access_token, reminder_id=reminder_id, status=reminder.status)
    reminder = await client().reminder_get(access_token=access_token, reminder_id=reminder_id)

    text = message_text_tools.get_reminder(reminder)
    keyboard = inline_kbs.edit_reminder(reminder, mode=mode, tags=tags)

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

    tag_id = call.model_dump()()['data'].split("_")[-1]
    reminder_id = call.model_dump()['data'].split("_")[-2]
    reminder = await client().reminder_get(access_token=access_token, reminder_id=reminder_id)
    reminder_tag_ids = reminder.tags + [tag_id]

    request = ReminderChangeTagsRequest.model_validate(
        {
            'id': reminder_id,
            'tags': reminder_tag_ids
        }
    )
    await client().reminder_post(access_token=access_token, request=request)

    reminder = await client().reminder_get(access_token=access_token, reminder_id=reminder_id)
    text = message_text_tools.get_reminder(reminder)

    keyboard = inline_kbs.edit_reminder(reminder, mode)

    await call.message.edit_text(text=text, reply_markup=keyboard, parse_mode="MarkdownV2")
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

    reminder_id = data['reminder_id']
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
        await state.update_data(mode=new_mode)
        return new_mode

    mode = await reset_mode_state()

    reminder_id = call.model_dump()['data'].split("_")[-1]
    await state.update_data(reminder_id=reminder_id)  # set reminder_id in state data

    reminder = await client().reminder_get(access_token=access_token, reminder_id=reminder_id)

    text = message_text_tools.get_reminder(reminder)
    keyboard = inline_kbs.edit_reminder(reminder, mode=mode)

    await call.message.edit_text(text=parse_for_markdown(text), reply_markup=keyboard, parse_mode="MarkdownV2")
    await bot.answer_callback_query(call.id)
