from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from aiogram.types import Message, CallbackQuery
from backend.bot.keyboards import inline_kbs, reply_kbs
from backend.bot.routers import start

from backend.bot.utils import get_message_reminders
from backend.bot.utils.message_text_tools import get_tags_edit
from backend.bot.utils.states import States

from backend.bot.clients import client

reminders_router = Router()


@reminders_router.message(StateFilter(States.reminder_menu),
                          F.text == "Редактировать тэги")
async def tags_edit(message: Message, state: FSMContext):
    data = await state.get_data()
    text = get_tags_edit(data=data)

    await message.answer(text=text,
                         reply_markup=inline_kbs.tag_menu_get_tags(data),
                         parse_mode="MarkdownV2")


@reminders_router.message(StateFilter(States.reminder_menu),
                          F.text == "Назад")
async def return_to_menu(message: Message, state: FSMContext):
    await state.set_state(States.start_menu)

    await message.answer(text="return to menu", reply_markup=reply_kbs.main_menu())


@reminders_router.callback_query(StateFilter(States.reminder_menu),
                                 F.data.startswith("reminder_next_"))
async def reminders_next(call: CallbackQuery, state: FSMContext):
    next_coef = int(call.dict()["data"].split("_")[-1])
    await state.update_data(next_coef=next_coef)

    data = await state.get_data()
    text = get_message_reminders(data=data)

    await call.message.edit_text(text=text,
                                 reply_markup=inline_kbs.reminders_buttons(data=data),
                                 parse_mode="MarkdownV2")


@reminders_router.callback_query(StateFilter(States.reminder_menu),
                                 F.data.startswith("reminder_previous_"))
async def reminders_previous(call: CallbackQuery, state: FSMContext):
    next_coef = int(call.dict()["data"].split("_")[-1])
    await state.update_data(next_coef=next_coef)

    data = await state.get_data()
    text = get_message_reminders(data=data)

    await call.message.edit_text(text=text,
                                 reply_markup=inline_kbs.reminders_buttons(data=data),
                                 parse_mode="MarkdownV2")


@reminders_router.callback_query(StateFilter(States.reminder_menu),
                                 F.data.startswith("reminder_day_filter_"))
async def reminders_day_filter(call: CallbackQuery, state: FSMContext):
    new_day = call.dict()["data"].split("_")[-1]

    await state.update_data(day=new_day)
    await state.update_data(next_coef=0)

    data = await state.get_data()
    text = get_message_reminders(data=data)

    await call.message.edit_text(text=text,
                                 reply_markup=inline_kbs.reminders_buttons(data=data),
                                 parse_mode="MarkdownV2")


@reminders_router.callback_query(StateFilter(States.reminder_menu),
                                 F.data == "reminder_tag_filter")
async def reminder_tag_filter(call: CallbackQuery, state: FSMContext):
    await state.update_data(tag_filter_click=1)

    data = await state.get_data()
    text = get_message_reminders(data)

    await call.message.edit_text(text=text,
                                 reply_markup=inline_kbs.reminders_buttons(data=data),
                                 parse_mode="MarkdownV2")


@reminders_router.callback_query(StateFilter(States.reminder_menu),
                                 F.data.startswith("reminder_tag_filter_back"))
async def reminder_tags_select(call: CallbackQuery, state: FSMContext):
    tag_filter = None
    tag_filter_click = 0
    await state.update_data(tag_filter=tag_filter)
    await state.update_data(tag_filter_click=tag_filter_click)

    data = await state.get_data()
    text = get_message_reminders(data)

    await call.message.edit_text(text=text,
                                 reply_markup=inline_kbs.reminders_buttons(data=data),
                                 parse_mode="MarkdownV2")


@reminders_router.callback_query(StateFilter(States.reminder_menu),
                                 F.data.startswith("reminder_tag_filter_"))
async def reminder_tags_select(call: CallbackQuery, state: FSMContext):
    tag_filter = call.dict()["data"].split("_")[-1]
    await state.update_data(tag_filter=tag_filter)

    data = await state.get_data()
    text = get_message_reminders(data)

    await call.message.edit_text(text=text,
                                 reply_markup=inline_kbs.reminders_buttons(data=data),
                                 parse_mode="MarkdownV2")


@reminders_router.callback_query(StateFilter(States.reminder_menu),
                                 F.data.startswith("reminder_edit_"))
async def reminder_edit(call: CallbackQuery, state: FSMContext):
    pass


@reminders_router.message(StateFilter(States.reminder_menu),
                          F.text == "Добавить напоминание")
async def add_reminder(message: Message, state: FSMContext):
    await state.update_data(add_reminder=1)

    text = ("Введите название вашего напоминания и когда вам нужно будет о нём напомнить. \n\n"
            "Также можете добавить тэг в виде эмодзи, с которым у вас ассоциируется ваше напоминание.\n\n"
            "Пример:\n — Завтра купить сигареты 🚬\n — 11 июля встреча одноклассников в 9 вечера 👔")
    await message.answer(text=text)


@reminders_router.message(StateFilter(States.reminder_menu))
async def add_reminder_check(message: Message, state: FSMContext):  # ЗАГЛУШКА обработать сообщение
    if message.text in ['Добавить напоминание', 'Назад', "Редактировать тэги"]:
        return

    reminder = message.text
    await message.answer(text=f"{reminder}\n\nЗдесь всё верно?",
                         reply_markup=inline_kbs.add_reminder_check(),
                         parse_mode="MarkdownV2")


@reminders_router.callback_query(StateFilter(States.reminder_menu),
                                 F.data.startswith("reminder_check_"))
async def add_reminder_check_answer(call: CallbackQuery, state: FSMContext):  # ЗАГЛУШКА закинуть в апи
    await state.update_data(add_reminder=0)

    answer = call.dict()["data"].split("_")[-1]
    if answer == "OK":
        # add to remindme_api

        text = "Напоминание добавлено\!"
        await call.message.edit_text(text=text,
                                     parse_mode="MarkdownV2")
    else:
        await call.message.delete()

    await start.reminders(message=call.message, state=state)
