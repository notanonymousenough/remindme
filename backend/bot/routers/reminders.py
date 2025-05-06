from typing import Annotated

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from backend.bot import bot
from backend.bot.clients import get_client_async
from backend.bot.clients.remindme_api import RemindMeApiClient
from backend.bot.keyboards import inline_kbs, reply_kbs
from backend.bot.routers.reminder_state_actions import add_reminder_process_1, add_reminder_process_2, \
    new_reminder_manual_process_1, new_reminder_manual_process_2, new_reminder_manual_process_3
from backend.bot.routers.reminder_state_actions.edit_reminder import reminder_edit_datetime_time_check
from backend.bot.routers.tag_state_actions import new_tag_process_1, new_tag_process_2, tag_edit_process_2
from backend.bot.routers.tag_state_actions.edit_tag import tags_edit
from backend.bot.utils import message_text_tools
from backend.bot.utils.depends import Depends
from backend.bot.utils.states import States

reminders_router = Router()


@reminders_router.message(StateFilter(States.reminder_menu))
async def route_reminder_message(message: Message, state: FSMContext):
    """
    Общий обработчик для States.reminder_menu (не только для этого роутера)
    """
    state_data = await state.get_data()
    action_type = state_data.get("action")
    message_answer = message.text

    match action_type:
        case "create_tag":
            pass
        case "edit_tag":
            pass
        case "reminder_change_time":
            await reminder_edit_datetime_time_check(message, state)
        case "new_tag_process_1":
            await new_tag_process_1(message=message, state=state)
        case "new_tag_process_2":
            await new_tag_process_2(message=message, state=state)
        case "tag_edit_process_2":
            await tag_edit_process_2(message=message, state=state)
        case "reminder_add":
            await add_reminder_process_2(message=message, state=state)
        case "new_reminder_manual_process_1":
            await new_reminder_manual_process_1(message=message, state=state)
        case "new_reminder_manual_process_2":
            await new_reminder_manual_process_2(message=message, state=state)
        case "new_reminder_manual_process_3":
            await new_reminder_manual_process_3(message=message, state=state)

    match message_answer:
        case "Назад":
            await state.update_data(action=None)
            await return_to_menu(message=message, state=state)
        case "Редактировать тэги":
            await state.update_data(action=None)
            await tags_edit(message=message, state=state)
        case "Добавить напоминание":
            await state.update_data(action=None)
            await add_reminder_process_1(message=message, state=state)
        case _:
            await message.answer("Не понимаю, что вы хотите сделать. Пожалуйста, выберите действие из меню.")


async def return_to_menu(message: Message, state: FSMContext):
    await state.set_state(States.start_menu)
    await message.reply(text="Возвращение в меню", reply_markup=reply_kbs.main_menu())


@reminders_router.callback_query(StateFilter(States.reminder_menu),
                                 F.data.startswith("reminder_next_"))
async def reminders_next(call: CallbackQuery,
                         state: FSMContext,
                         client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    next_coef = int(call.dict()["data"].split("_")[-1])
    await state.update_data(next_coef=next_coef)

    data = await state.get_data()

    access_token = data["access_token"]

    reminders = sorted((await client().reminders_get(state_data=data)), key=lambda x: x["time"])
    tags = await client().tags_get(access_token=access_token)

    text = message_text_tools.get_reminders(
        reminders=reminders,
        next_coef=data['next_coef'],
        strip=data["strip"],
        day=data["day"],
        tag_filter=data["tag_filter"]
    )

    await call.message.edit_text(text=text,
                                 reply_markup=inline_kbs.reminders_buttons(reminders=reminders,
                                                                           next_coef=data['next_coef'],
                                                                           day_filter=data["day"],
                                                                           tag_filter_is_click=data["tag_filter_click"],
                                                                           tags=tags),
                                 parse_mode="MarkdownV2")
    await bot.answer_callback_query(call.id)


@reminders_router.callback_query(StateFilter(States.reminder_menu),
                                 F.data.startswith("reminder_previous_"))
async def reminders_previous(call: CallbackQuery,
                             state: FSMContext,
                             client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    next_coef = int(call.dict()["data"].split("_")[-1])
    await state.update_data(next_coef=next_coef)

    data = await state.get_data()
    access_token = data["access_token"]

    tags = await client().tags_get(access_token=access_token)
    reminders = sorted((await client().reminders_get(state_data=data)), key=lambda x: x["time"])
    text = message_text_tools.get_reminders(
        reminders=reminders,
        next_coef=data['next_coef'],
        strip=data["strip"],
        day=data["day"],
        tag_filter=data["tag_filter"]
    )

    await call.message.edit_text(text=text,
                                 reply_markup=inline_kbs.reminders_buttons(reminders=reminders,
                                                                           next_coef=data['next_coef'],
                                                                           day_filter=data["day"],
                                                                           tag_filter_is_click=data["tag_filter_click"],
                                                                           tags=tags),
                                 parse_mode="MarkdownV2")
    await bot.answer_callback_query(call.id)


@reminders_router.callback_query(StateFilter(States.reminder_menu),
                                 F.data.startswith("reminder_day_filter_"))
async def reminders_day_filter(call: CallbackQuery,
                               state: FSMContext,
                               client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    new_day = call.dict()["data"].split("_")[-1]
    next_coef = 0
    await state.update_data(day=new_day)
    await state.update_data(next_coef=next_coef)

    data = await state.get_data()
    access_token = data["access_token"]

    tags = await client().tags_get(access_token=access_token)
    reminders = sorted((await client().reminders_get(state_data=data)), key=lambda x: x["time"])
    text = message_text_tools.get_reminders(
        reminders=reminders,
        next_coef=data['next_coef'],
        strip=data["strip"],
        day=data["day"],
        tag_filter=data["tag_filter"]
    )

    await call.message.edit_text(text=text,
                                 reply_markup=inline_kbs.reminders_buttons(reminders=reminders,
                                                                           next_coef=data['next_coef'],
                                                                           day_filter=data["day"],
                                                                           tag_filter_is_click=data["tag_filter_click"],
                                                                           tags=tags),
                                 parse_mode="MarkdownV2")
    await bot.answer_callback_query(call.id)


@reminders_router.callback_query(StateFilter(States.reminder_menu),
                                 F.data == "reminder_tag_filter")
async def reminder_tag_filter(call: CallbackQuery,
                              state: FSMContext,
                              client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    await state.update_data(tag_filter_click=1)

    data = await state.get_data()

    access_token = data["access_token"]

    tags = await client().tags_get(access_token=access_token)
    reminders = sorted((await client().reminders_get(state_data=data)), key=lambda x: x["time"])

    text = message_text_tools.get_reminders(
        reminders=reminders,
        next_coef=data['next_coef'],
        strip=data["strip"],
        day=data["day"],
        tag_filter=data["tag_filter"]
    )

    await call.message.edit_text(text=text,
                                 reply_markup=inline_kbs.reminders_buttons(reminders=reminders,
                                                                           next_coef=data['next_coef'],
                                                                           day_filter=data["day"],
                                                                           tag_filter_is_click=data["tag_filter_click"],
                                                                           tags=tags),
                                 parse_mode="MarkdownV2")
    await bot.answer_callback_query(call.id)


@reminders_router.callback_query(StateFilter(States.reminder_menu),
                                 F.data.startswith("reminder_tag_filter_back"))
async def reminder_tags_select(call: CallbackQuery,
                               state: FSMContext,
                               client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    tag_filter = None
    tag_filter_click = 0
    await state.update_data(tag_filter=tag_filter)
    await state.update_data(tag_filter_click=tag_filter_click)

    data = await state.get_data()

    access_token = data["access_token"]

    tags = await client().tags_get(access_token=access_token)
    reminders = sorted((await client().reminders_get(state_data=data)), key=lambda x: x["time"])

    text = message_text_tools.get_reminders(
        reminders=reminders,
        next_coef=data['next_coef'],
        strip=data["strip"],
        day=data["day"],
        tag_filter=data["tag_filter"]
    )

    await call.message.edit_text(text=text,
                                 reply_markup=inline_kbs.reminders_buttons(reminders=reminders,
                                                                           next_coef=data['next_coef'],
                                                                           day_filter=data["day"],
                                                                           tag_filter_is_click=data["tag_filter_click"],
                                                                           tags=tags),
                                 parse_mode="MarkdownV2")
    await bot.answer_callback_query(call.id)


@reminders_router.callback_query(StateFilter(States.reminder_menu),
                                 F.data.startswith("reminder_tag_filter_"))
async def reminder_tags_filter_select(call: CallbackQuery,
                                      state: FSMContext,
                                      client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    tag_filter = call.dict()["data"].split("_")[-1]
    await state.update_data(tag_filter=tag_filter)

    data = await state.get_data()

    access_token = data["access_token"]

    tags = await client().tags_get(access_token=access_token)
    reminders = sorted((await client().reminders_get(state_data=data)), key=lambda x: x["time"])

    text = message_text_tools.get_reminders(
        reminders=reminders,
        next_coef=data['next_coef'],
        strip=data["strip"],
        day=data["day"],
        tag_filter=tag_filter
    )

    await call.message.edit_text(text=text,
                                 reply_markup=inline_kbs.reminders_buttons(reminders=reminders,
                                                                           next_coef=data['next_coef'],
                                                                           day_filter=data["day"],
                                                                           tag_filter_is_click=data["tag_filter_click"],
                                                                           tags=tags),
                                 parse_mode="MarkdownV2")
    await bot.answer_callback_query(call.id)
