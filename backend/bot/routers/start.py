from typing import Annotated

from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from backend.bot.clients import get_client_async
from backend.bot.clients.remindme_api import RemindMeApiClient
from backend.bot.keyboards import reply_kbs, inline_kbs
from backend.bot.utils import States, message_text_tools
from backend.bot.utils.depends import Depends
from backend.bot.utils.parse_markdown_text import parse_for_markdown
from backend.bot.utils.state_data_tools import state_data_reset

start_router = Router()


@start_router.message(CommandStart())
async def start_menu(message: Message, state: FSMContext, client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    await state.set_state(States.start_menu)
    data = await state.get_data()
    access_token = data["access_token"]

    keyboard = None

    user = await client().user_get(access_token)
    if user.timezone:
        await state.update_data(timezone=user.timezone)
        text = "Привет!\n\nУправление ботом через клавиатуру снизу :)"
    else:
        text = "Привет! Необходимо выбрать свой часовой пояс:"
        # keyboard = inline_kbs....... stalo lenb pisat kod na etom meste

    await message.answer(text=parse_for_markdown(text),
                         reply_markup=reply_kbs.main_menu())


@start_router.message(F.text == "Напоминания")
async def reminders(message: Message,
                    state: FSMContext,
                    client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    data = await state.get_data()
    access_token = data["access_token"]
    timezone = data['timezone']

    if (await state.get_state()) != States.reminder_menu:
        await state.set_state(States.reminder_menu)  # set state for reminders menu
        await state_data_reset(state=state, telegram_id=message.from_user.id, access_token=access_token, timezone=timezone)

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

    await message.answer(text="Вывожу список напоминаний..", reply_markup=reply_kbs.reminders_menu())
    await message.answer(text=text,
                         reply_markup=inline_kbs.reminders_buttons(reminders=reminders,
                                                                   next_coef=data['next_coef'],
                                                                   day_filter=data["day"],
                                                                   tag_filter_is_click=data["tag_filter_click"],
                                                                   tags=tags),
                         parse_mode="MarkdownV2")


@start_router.message(F.text == "Привычки")
async def habits(message: Message,
                 state: FSMContext,
                 client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    access_token = (await state.get_data())["access_token"]
    await state.set_state(States.habits_menu)
    data = await state.get_data()
    await state.set_data({
        "user_id": message.from_user.id,
        "action": None,
        "access_token": access_token,
        "next_coef": 0,
        "timezone": data['timezone']
    })

    data = await state.get_data()

    next_coef = data["next_coef"]
    habits = sorted((await client().habits_get(state_data=data)), key=lambda x: x.updated_at)
    text = message_text_tools.get_habits(habits=habits)

    await message.answer(text="Вывожу список привычек..", reply_markup=reply_kbs.habits_menu())
    await message.answer(text=text,
                         reply_markup=inline_kbs.get_habits_buttons(habits=habits, next_coef=next_coef),
                         parse_mode="MarkdownV2")


@start_router.message(F.text == "Прогресс")
async def progress():
    pass
    # TODO прогресс на день. возможно следует переименовать в "ЗАДАЧИ"?


@start_router.message(StateFilter(States.start_menu))
async def text_from_user(message: Message, state: FSMContext):
    await start_menu(message, state)
