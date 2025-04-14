from typing import Annotated

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from backend.bot.clients import get_client_async
from backend.bot.clients.remindme_api import RemindMeApiClient
from backend.bot.keyboards import reply_kbs
from backend.bot.keyboards.reply_kbs import HABITS_ADD_PROCESS, HABITS_ADD_PROCESS_INTERVALS
from backend.bot.routers import start
from backend.bot.utils.depends import Depends
from backend.bot.utils.states import States
from backend.control_plane.schemas.requests.habit import HabitSchemaPostRequest

new_habit_router = Router()


@new_habit_router.message(StateFilter(States.habits_menu),
                          F.text == "Добавить привычку")
async def habit_add_process_start(message: Message, state: FSMContext):
    text = "🧩 Как будет называться привычка\?"

    await state.update_data(action="add_habit_process_1")
    await message.answer(text=text,
                         parse_mode="MarkdownV2")


@new_habit_router.message(StateFilter(States.habits_menu))
async def habit_add_process_1(message: Message, state: FSMContext):
    data = await state.get_data()
    if data["action"] == "habit_add_process_end":
        text = f"❌ Допустимые значения: {" ".join([action_text for action_text in HABITS_ADD_PROCESS])}"
    else:
        await state.update_data(add_habit_name=message.text)
        await state.update_data(action="add_habit_process_end")
        text = "🧩 Как часто хочешь ее выполнять?\."

    await message.answer(text=text,
                         reply_markup=reply_kbs.habits_add_process(),
                         parse_mode="MarkdownV2")


@new_habit_router.message(StateFilter(States.habits_menu),
                          F.text.in_(HABITS_ADD_PROCESS))
async def habit_add_process_end(message: Message,
                                state: FSMContext,
                                client=Annotated[RemindMeApiClient, Depends(get_client_async)]):
    data = await state.get_data()
    habit_request = HabitSchemaPostRequest.model_validate(
        {
            "text": data["add_habit_name"],
            "interval": HABITS_ADD_PROCESS_INTERVALS[message.text],
        }
    )
    if await client().habit_post(state_data=data, habit_request=habit_request):
        text = "Привычка успешно добавлена\!"
    else:
        text = "Ошибка при отправке данных на сервер\.\."

    await state.update_data(action=None)
    await message.answer(text=text,
                         reply_markup=reply_kbs.habits_menu(),
                         parse_mode="MarkdownV2")
    await start.habits(message, state)
