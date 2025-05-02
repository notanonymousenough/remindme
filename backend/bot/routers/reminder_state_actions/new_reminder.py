import datetime
from typing import Annotated

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from backend.bot import bot
from backend.bot.clients import get_client_async
from backend.bot.clients.remindme_api import RemindMeApiClient
from backend.bot.keyboards import reply_kbs, inline_kbs
from backend.bot.routers import start
from backend.bot.utils import States, date_formatting
from backend.bot.utils.depends import Depends
from backend.bot.utils.date_formatting import parse_relative_date
from backend.bot.utils.parse_markdown_text import parse_for_markdown
from backend.control_plane.schemas.requests.reminder import ReminderAddSchemaRequest

new_reminder_router = Router(name="add_reminder")


async def add_reminder_process_1(message: Message,
                                 state: FSMContext):
    await state.update_data(action="reminder_add")

    text = ("Введите название вашего напоминания и когда вам нужно будет о нём напомнить. \n\n"
            "Также можете добавить тэг в виде эмодзи, с которым у вас ассоциируется ваше напоминание.\n\n"
            "Пример:\n — Завтра купить сигареты 🚬\n — 11 июля встреча одноклассников в 9 вечера 👔")
    await message.answer(text=text)


@new_reminder_router.message(StateFilter(States.reminder_menu))
async def add_reminder_process_2(message: Message, state: FSMContext):
    if message.text in reply_kbs.REMINDERS_MENU_TEXTS:
        return

    # TODO запрос в control_plane/utils/yandex_gpt_api

    reminder_text = message.text
    time_text = None

    tag_text = None
    # TODO также выбирается имя тега (нейросетью), если он есть, и отправляется в ручку апи в след ручке здесь

    text = reminder_text + str(time_text) + str(tag_text)  # example for text constructor

    await message.answer(text=f"{reminder_text}\n\nЗдесь всё верно?",
                         reply_markup=inline_kbs.add_reminder_check(),
                         parse_mode="MarkdownV2")


@new_reminder_router.callback_query(StateFilter(States.reminder_menu),
                                    F.data.startswith("reminder_check_"))
async def add_reminder_process_3(call: CallbackQuery,
                                 state: FSMContext,
                                 client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    data = await state.get_data()

    answer = call.dict()["data"].split("_")[-1]
    if answer == "OK":
        # TODO: add to control_plane
        text = "Напоминание добавлено!"
    elif answer == "MANUAL":
        text = "Ручной режим: \n\nКак будет называться ваше напоминания?"
        await state.update_data(action="new_reminder_manual_process_1")
    else:
        text = "Создание напоминания отменено."

    if answer != "CANCEL":
        await bot.send_message(chat_id=call.message.chat.id, text=parse_for_markdown(text), parse_mode="MarkdownV2")
        await bot.answer_callback_query(call.id)
    else:
        await start.reminders(message=call.message, state=state)


async def new_reminder_manual_process_1(message: Message, state: FSMContext):
    await state.update_data(action="new_reminder_manual_process_2")
    await state.update_data(add_reminder_manual_text=message.text)

    text = ("Теперь введи дату, когда его прислать в формате ДД.ММ.ГГГГ или ключевым словом (завтра, послезавтра, "
            "через неделю...)")

    await message.reply(text=parse_for_markdown(text), parse_mode="MarkdownV2")


async def new_reminder_manual_process_2(message: Message,
                                        state: FSMContext):
    date = parse_relative_date(date=message.text)

    if date:
        await state.update_data(action="new_reminder_manual_process_3")
        await state.update_data(add_reminder_manual_date=date)
        text = "Во сколько времени напомнить?"
    else:
        text = "Ошибка формата даты.. возврат"
        await state.update_data(action=None)

    await message.reply(text=parse_for_markdown(text), parse_mode="MarkdownV2")


async def new_reminder_manual_process_3(message: Message,
                                        state: FSMContext,
                                        client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    data = await state.get_data()
    access_token = data['access_token']
    add_reminder_manual_text = data["add_reminder_manual_text"]
    add_reminder_manual_date = data["add_reminder_manual_date"]
    time = message.text

    try:
        add_reminder_manual_time = date_formatting.get_correct_time(time)
        request = {
            "text": add_reminder_manual_text,
            "time": datetime.datetime.combine(add_reminder_manual_date, add_reminder_manual_time),
            "tags": []
        }
        request = ReminderAddSchemaRequest.model_validate(request)

        if await client().reminder_post(access_token=access_token, request=request):
            text = "Напоминание успешно добавлено!"
        else:
            text = "Ошибка отправки на сервер.. возврат"
    except Exception as ex:
        print(ex)
        text = "Ошибка формата напоминания.. возврат"

    await message.reply(text=parse_for_markdown(text), parse_mode="MarkdownV2")
    await start.reminders(message=message, state=state)
