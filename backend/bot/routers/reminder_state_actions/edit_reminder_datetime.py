from datetime import datetime
from typing import Annotated

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from backend.bot import bot
from backend.bot.clients.remindme_api import RemindMeApiClient, get_client_async
from backend.bot.keyboards import inline_kbs
from backend.bot.routers.reminder_state_actions.edit_reminder import _reminder_edit
from backend.bot.utils import States, date_formatting
from backend.bot.utils.depends import Depends
from backend.control_plane.schemas.requests.reminder import ReminderEditTimeRequest

edit_reminder_datetime_router = Router()


@edit_reminder_datetime_router.callback_query(StateFilter(States.reminder_menu),
                                     F.data.startswith("reminder_edit_datetime_time"))
async def reminder_edit_datetime_time(call: CallbackQuery,
                                      state: FSMContext,
                                      client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    text = "Введи новое время, например 14:00 или 2 часа дня"

    await state.update_data(action="reminder_edit_time")

    await call.message.edit_text(text=text)
    await bot.answer_callback_query(call.id)


@edit_reminder_datetime_router.callback_query(StateFilter(States.reminder_menu),
                                     F.data.startswith("reminder_edit_datetime_date"))
async def reminder_edit_datetime_date(call: CallbackQuery,
                                      state: FSMContext,
                                      client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    text = "Введи новую дату в любом формате"

    await state.update_data(action="reminder_edit_date")

    await call.message.edit_text(text=text)
    await bot.answer_callback_query(call.id)


@edit_reminder_datetime_router.message(StateFilter(States.reminder_menu))
async def reminder_edit_datetime_time_check(message: Message,
                                            state: FSMContext,
                                            client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    data = await state.get_data()
    reminder_id = data["reminder_edit_id"]
    access_token = data["access_token"]

    text = "Время напоминания НЕ обновлено."
    try:
        reminder = await client().reminder_get(access_token, reminder_id)

        old_datetime = reminder.time
        new_time = date_formatting.get_correct_time(message.text)
        new_datetime = datetime.combine(date=old_datetime.date(), time=new_time)

        request = ReminderEditTimeRequest.model_validate(
            {
                "id": reminder_id,
                "time": new_datetime,
            }
        )
        await client().reminder_postpone(access_token=access_token, request=request)

        text = "Время напоминания обновлено!\n\n"
    except Exception as ex:
        print(ex)
        text = "Неверный формат времени\n\n"
    finally:
        await _reminder_edit(message, state, text=text)


@edit_reminder_datetime_router.message(StateFilter(States.reminder_menu))
async def reminder_edit_datetime_date_check(message: Message,
                                            state: FSMContext,
                                            client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    data = await state.get_data()
    access_token = data["access_token"]
    reminder_id = data['reminder_edit_id']

    try:
        reminder = await client().reminder_get(access_token, reminder_id)
        reminder_old_datetime = reminder.time
        new_date = date_formatting.get_correct_date(message.text)
        new_datetime = datetime.combine(date=new_date, time=reminder_old_datetime.time())

        request = ReminderEditTimeRequest.model_validate(
            {
                "id": reminder_id,
                "time": new_datetime,
            }
        )
        await client().reminder_postpone(access_token=access_token, request=request)
        text = "Дата напоминания обновлена!\n\n"
    except Exception as ec:
        print(ec)
        text = "Неверный формат даты\n\n"

    await _reminder_edit(message, state, text=text)


@edit_reminder_datetime_router.callback_query(StateFilter(States.reminder_menu),
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
