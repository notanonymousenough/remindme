from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext

from aiogram.types import Message, CallbackQuery
from backend.bot.keyboards import inline_kbs, reply_kbs

from backend.bot.utils import get_message_reminders
from backend.bot.utils.states import States

from backend.bot.clients import client

reminders_router = Router()


@reminders_router.callback_query(StateFilter(States.reminder_menu), F.data.startswith("reminder_next_"))
async def menu_next(call: CallbackQuery, state: FSMContext):
    next_coef = int(call.dict()["data"].split("_")[-1])
    # change later: next_count will be written by state, not from call

    await state.update_data(next_coef=next_coef)

    data = await state.get_data()

    text = get_message_reminders(data=data)
    await call.message.edit_text(text=text,
                                reply_markup=inline_kbs.reminders_buttons(data=data),
                                parse_mode="MarkdownV2")


@reminders_router.callback_query(StateFilter(States.reminder_menu), F.data.startswith("reminder_previous_"))
async def menu_next(call: CallbackQuery, state: FSMContext):
    next_coef = int(call.dict()["data"].split("_")[-1])

    await state.update_data(next_coef=next_coef)

    data = await state.get_data()

    text = get_message_reminders(data=data)
    await call.message.edit_text(text=text,
                                reply_markup=inline_kbs.reminders_buttons(data=data),
                                parse_mode="MarkdownV2")


@reminders_router.callback_query(StateFilter(States.reminder_menu), F.data.startswith("reminder_filter_"))
async def show_reminder(call: CallbackQuery, state: FSMContext):
    new_day = call.dict()["data"].split("_")[-1]

    await state.update_data(day=new_day)

    data = await state.get_data()

    text = get_message_reminders(data=data)
    await call.message.edit_text(text=text,
                                 reply_markup=inline_kbs.reminders_buttons(data=data),
                                 parse_mode="MarkdownV2")


@reminders_router.message(StateFilter(States.reminder_menu), F.text == "Фильтрация по тэгам")
async def reminder_tags(message: Message, state: FSMContext):
    await message.answer(text="134134")


@reminders_router.message(StateFilter(States.reminder_menu), F.text == "Добавить напоминание")
async def add_reminder(message: Message, state: FSMContext):
    pass


@reminders_router.message(StateFilter(States.reminder_menu), F.text == "Назад")
async def return_to_menu(message: Message, state: FSMContext):
    await state.set_state(States.start_menu)

    await message.answer(text="return to menu", reply_markup=reply_kbs.main_menu())
