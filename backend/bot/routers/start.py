from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from backend.bot.keyboards import reply_kbs, inline_kbs
from backend.bot.utils import States, get_message_habits, message_text_tools

from backend.bot.clients import client

start_router = Router()


@start_router.message(CommandStart())
async def start_menu(message: Message, state: FSMContext):
    await state.set_state(States.start_menu)
    await message.answer(text="Привет!\n\nУправление ботом через клавиатуру снизу :)",
                         reply_markup=reply_kbs.main_menu())


@start_router.message(F.text == "Напоминания")
async def reminders(message: Message, state: FSMContext):
    if (await state.get_state()) != States.reminder_menu:
        await state.set_state(States.reminder_menu)  # set state for reminders menu
        await state.set_data({
            "day": "today",
            "user_id": message.from_user.id,
            "day_filter": "today",
            "next_coef": 0,
            "strip": [0, 5],
            "tag_filter_click": 0,
            "tag_filter": None,
            "add_reminder": 0
        })

    data = await state.get_data()
    day_filter = data["day"]
    next_coef = data['next_coef']
    tag_filter_is_click = data["tag_filter_click"]
    tags = client.get_tags()
    day = data["day"]
    tag_filter = data["tag_filter"]
    strip = data["strip"]
    reminders = sorted(client.get_reminders(day, tag_filter), key=lambda x: x["time_exp"])
    text = message_text_tools.get_message_reminders(
        reminders=reminders,
        next_coef=next_coef,
        strip=strip,
        day=day,
        tag_filter=tag_filter
    )

    await message.answer(text="Вывожу список напоминаний..", reply_markup=reply_kbs.reminders_menu())
    await message.answer(text=text,
                         reply_markup=inline_kbs.reminders_buttons(reminders=reminders,
                                                                   next_coef=next_coef,
                                                                   day_filter=day_filter,
                                                                   tag_filter_is_click=tag_filter_is_click,
                                                                   tags=tags
                                                                   ),
                         parse_mode="MarkdownV2")


@start_router.message(F.text == "Привычки")
async def habits(message: Message, state: FSMContext):
    await state.set_state(States.habits_menu)
    await state.set_data({
        "user_id": message.from_user.id,
        "habit_add": 0
    })

    data = await state.get_data()
    habits = client.get_habits(data=data)
    text = get_message_habits(habits=habits)

    await message.answer(text="Вывожу список привычек..", reply_markup=reply_kbs.habits_menu())
    await message.answer(text=text,
                         reply_markup=inline_kbs.get_habits_buttons(habits=habits),
                         parse_mode="MarkdownV2")


@start_router.message(F.text == "Прогресс")
async def progress():
    pass


@start_router.message(StateFilter(States.start_menu))
async def text_from_user(message: Message, state: FSMContext):
    await start_menu(message, state)
