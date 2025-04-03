from typing import Annotated

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from aiogram.types import Message, CallbackQuery

from backend.bot import bot
from backend.bot.clients import get_client_async
from backend.bot.clients.remindme_api import RemindMeApiClient

from backend.bot.keyboards import inline_kbs, reply_kbs
from backend.bot.routers import start

from backend.bot.utils import message_text_tools
from backend.bot.utils.depends import Depends
from backend.bot.utils.states import States

reminders_router = Router()


@reminders_router.message(StateFilter(States.reminder_menu),
                          F.text == "Редактировать тэги")
async def tags_edit(message: Message,
                    state: FSMContext,
                    client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    data = await state.get_data()

    # tags = client.get_tags() TODO()
    text = message_text_tools.get_tags_edit(tags=tags)

    await message.answer(text=text,
                         reply_markup=inline_kbs.tag_menu_get_tags(tags=tags),
                         parse_mode="MarkdownV2")


@reminders_router.callback_query(StateFilter(States.reminder_menu),
                                 F.data.startswith("tags_edit_"))
async def tags_edit_(call: CallbackQuery, state: FSMContext):  # TODO(Arsen): add edit to tags
    data = await state.get_data()
    text = ""

    await call.answer(text=text,
                      parse_mode="MarkdownV2")


@reminders_router.message(StateFilter(States.reminder_menu),
                          F.text == "Назад")
async def return_to_menu(message: Message, state: FSMContext):
    await state.set_state(States.start_menu)

    await message.answer(text="return to menu", reply_markup=reply_kbs.main_menu())


@reminders_router.callback_query(StateFilter(States.reminder_menu),
                                 F.data.startswith("reminder_next_"))
async def reminders_next(call: CallbackQuery,
                         state: FSMContext,
                         client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    next_coef = int(call.dict()["data"].split("_")[-1])
    await state.update_data(next_coef=next_coef)

    data = await state.get_data()
    strip = data['strip']
    day_filter = data["day"]
    tag_filter = data["tag_filter"]
    tag_filter_is_click = data["tag_filter_click"]
    day = data["day"]
    reminders = sorted((await client().get_reminders(state_data=data)), key=lambda x: x["time"])
    tags = client.get_tags()
    text = message_text_tools.get_message_reminders(
        reminders=reminders,
        next_coef=next_coef,
        strip=strip,
        day=day_filter,
        tag_filter=tag_filter
    )

    await call.message.edit_text(text=text,
                                 reply_markup=inline_kbs.reminders_buttons(reminders=reminders,
                                                                           next_coef=next_coef,
                                                                           day_filter=day_filter,
                                                                           tag_filter_is_click=tag_filter_is_click,
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
    day_filter = data["day"]
    tag_filter_is_click = data["tag_filter_click"]
    strip = data["strip"]
    tag_filter = data["tag_filter"]
    tags = client.get_tags()
    day = data["day"]
    reminders = sorted((await client().get_reminders(state_data=data)), key=lambda x: x["time"])
    text = message_text_tools.get_message_reminders(
        reminders=reminders,
        next_coef=next_coef,
        strip=strip,
        day=day_filter,
        tag_filter=tag_filter
    )

    await call.message.edit_text(text=text,
                                 reply_markup=inline_kbs.reminders_buttons(reminders=reminders,
                                                                           next_coef=next_coef,
                                                                           day_filter=day_filter,
                                                                           tag_filter_is_click=tag_filter_is_click,
                                                                           tags=tags),
                                 parse_mode="MarkdownV2")
    await bot.answer_callback_query(call.id)


@reminders_router.callback_query(StateFilter(States.reminder_menu),
                                 F.data.startswith("reminder_day_filter_"))
async def reminders_day_filter(call: CallbackQuery,
                               state: FSMContext,
                               client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    new_day = call.dict()["data"].split("_")[-1]

    await state.update_data(day=new_day)
    await state.update_data(next_coef=0)

    data = await state.get_data()
    next_coef = data['next_coef']
    day_filter = data["day"]
    tag_filter_is_click = data["tag_filter_click"]
    strip = data['strip']
    tag_filter = data["tag_filter"]
    # tags = client.get_tags() TODO
    tags = None
    day = data["day"]
    reminders = sorted((await client().get_reminders(state_data=data)), key=lambda x: x["time"])
    text = message_text_tools.get_message_reminders(
        reminders=reminders,
        next_coef=next_coef,
        strip=strip,
        day=day_filter,
        tag_filter=tag_filter
    )

    await call.message.edit_text(text=text,
                                 reply_markup=inline_kbs.reminders_buttons(reminders=reminders,
                                                                           next_coef=next_coef,
                                                                           day_filter=day_filter,
                                                                           tag_filter_is_click=tag_filter_is_click,
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
    next_coef = data['next_coef']
    day_filter = data["day"]
    tag_filter_is_click = data["tag_filter_click"]
    strip = data["strip"]
    tag_filter = data["tag_filter"]
    tags = client.get_tags()
    day = data["day"]
    reminders = sorted((await client().get_reminders(state_data=data)), key=lambda x: x["time"])
    text = message_text_tools.get_message_reminders(
        reminders=reminders,
        next_coef=next_coef,
        strip=strip,
        day=day_filter,
        tag_filter=tag_filter
    )

    await call.message.edit_text(text=text,
                                 reply_markup=inline_kbs.reminders_buttons(reminders=reminders,
                                                                           next_coef=next_coef,
                                                                           day_filter=day_filter,
                                                                           tag_filter_is_click=tag_filter_is_click,
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
    next_coef = data['next_coef']
    day_filter = data["day"]
    tag_filter_is_click = data["tag_filter_click"]
    tags = client.get_tags()
    strip = data["strip"]
    day = data["day"]
    reminders = sorted((await client().get_reminders(state_data=data)), key=lambda x: x["time"])
    text = message_text_tools.get_message_reminders(
        reminders=reminders,
        next_coef=next_coef,
        strip=strip,
        day=day_filter,
        tag_filter=tag_filter
    )

    await call.message.edit_text(text=text,
                                 reply_markup=inline_kbs.reminders_buttons(reminders=reminders,
                                                                           next_coef=next_coef,
                                                                           day_filter=day_filter,
                                                                           tag_filter_is_click=tag_filter_is_click,
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
    next_coef = data['next_coef']
    day_filter = data["day"]
    tag_filter_is_click = data["tag_filter_click"]
    # tags = client.get_tags() TODO()
    day = data["day"]
    strip = data["strip"]
    reminders = sorted((await client().get_reminders(state_data=data)), key=lambda x: x["time"])
    text = message_text_tools.get_message_reminders(
        reminders=reminders,
        next_coef=next_coef,
        strip=strip,
        day=day_filter,
        tag_filter=tag_filter
    )

    await call.message.edit_text(text=text,
                                 reply_markup=inline_kbs.reminders_buttons(reminders=reminders,
                                                                           next_coef=next_coef,
                                                                           day_filter=day_filter,
                                                                           tag_filter_is_click=tag_filter_is_click,
                                                                           tags=tags),
                                 parse_mode="MarkdownV2")
    await bot.answer_callback_query(call.id)


@reminders_router.callback_query(StateFilter(States.reminder_menu),
                                 F.data.startswith("reminder_edit_"))
async def reminder_edit(call: CallbackQuery,
                        state: FSMContext,
                        client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    await bot.answer_callback_query(call.id)


@reminders_router.message(StateFilter(States.reminder_menu),
                          F.text == "Добавить напоминание")
async def add_reminder(message: Message,
                       state: FSMContext):
    await state.update_data(add_reminder=1)

    text = ("Введите название вашего напоминания и когда вам нужно будет о нём напомнить. \n\n"
            "Также можете добавить тэг в виде эмодзи, с которым у вас ассоциируется ваше напоминание.\n\n"
            "Пример:\n — Завтра купить сигареты 🚬\n — 11 июля встреча одноклассников в 9 вечера 👔")
    await message.answer(text=text)


@reminders_router.message(StateFilter(States.reminder_menu))
async def add_reminder_check(message: Message, state: FSMContext):  # TODO(Arsen): ЗАГЛУШКА обработать сообщение
    if message.text in reply_kbs.REMINDERS_MENU_TEXTS:
        return
    # TODO запрос в control_plane/utils/yandex_gpt_api

    # TODO также выбирается имя тега, если он есть, и отправляется в ручку апи в след ручке здесь
    reminder_text = message.text
    await message.answer(text=f"{reminder_text}\n\nЗдесь всё верно?",
                         reply_markup=inline_kbs.add_reminder_check(),
                         parse_mode="MarkdownV2")


@reminders_router.callback_query(StateFilter(States.reminder_menu),
                                 F.data.startswith("reminder_check_"))
async def add_reminder_check_answer(call: CallbackQuery,
                                    state: FSMContext,
                                    client=Annotated[RemindMeApiClient, Depends(get_client_async)]):  # TODO(ARSEN): закинуть в апи
    await state.update_data(add_reminder=0)

    answer = call.dict()["data"].split("_")[-1]
    if answer == "OK":
        # add to control_plane

        text = "Напоминание добавлено\!"
        await call.message.edit_text(text=text,
                                     parse_mode="MarkdownV2")
        await bot.answer_callback_query(call.id)
    else:
        await call.message.delete()

    await start.reminders(message=call.message, state=state)
    await bot.answer_callback_query(call.id)
