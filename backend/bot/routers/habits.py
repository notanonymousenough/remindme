from typing import Annotated

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from aiogram.types import Message, CallbackQuery

from backend.bot import bot
from backend.bot.clients import get_client_async
from backend.bot.clients.remindme_api import RemindMeApiClient
from backend.bot.keyboards import inline_kbs, reply_kbs
from backend.bot.keyboards.reply_kbs import HABITS_ADD_PROCESS, HABITS_ADD_PROCESS_INTERVALS
from backend.bot.routers import start as start_router
from backend.bot.utils.depends import Depends

from backend.bot.utils.states import States
from backend.control_plane.schemas.requests.habit import HabitSchemaPostRequest

habits_router = Router()


@habits_router.message(StateFilter(States.habits_menu),
                       F.text == "Назад")
async def return_to_menu(message: Message, state: FSMContext):
    await state.set_state(States.start_menu)

    text = "Перемещаемся в главное меню\.\."

    await message.answer(text=text,
                         reply_markup=reply_kbs.main_menu(),
                         parse_mode="MarkdownV2")


@habits_router.message(StateFilter(States.habits_menu),
                       F.text == "Добавить привычку")
async def habit_add_process_start(message: Message, state: FSMContext):
    text = "🧩 Как будет называться привычка\?"

    await state.update_data(action="add_habit_process_1")
    await message.answer(text=text,
                         parse_mode="MarkdownV2")


@habits_router.message(StateFilter(States.habits_menu))
async def habit_add_process_1(message: Message, state: FSMContext):
    data = await state.get_data()
    if data["action"] == "add_habit_process_2":
        text = f"❌ Допустимые значения: {" ".join([action_text for action_text in HABITS_ADD_PROCESS])}"
    else:
        await state.update_data(add_habit_name=message.text)
        await state.update_data(action="add_habit_process_2")
        text = "🧩 Как часто хочешь ее выполнять?\."

    await message.answer(text=text,
                         reply_markup=reply_kbs.habits_add_process(),
                         parse_mode="MarkdownV2")


@habits_router.message(StateFilter(States.habits_menu),
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
    if await client().habits_post(state_data=data, habit_request=habit_request):
        text = "Привычка успешно добавлена\!"
    else:
        text = "Ошибка при отправке данных на сервер\.\."

    await state.update_data(action=0)
    await message.answer(text=text,
                         parse_mode="MarkdownV2")
    await start_router.habits(message=message, state=state)


@habits_router.callback_query(StateFilter(States.habits_menu),
                              F.data.startswith("habit_edit_"))
async def habit_edit(call: CallbackQuery, state: FSMContext):
    data = state.get_data()

    await call.message.answer(text="разработчик еще не сделал редактирование привычек)")
    await bot.answer_callback_query(call.id)


@habits_router.message(StateFilter(States.habits_menu))
async def habits_get(message: Message, state: FSMContext):
    await start_router.habits(message=message, state=state)
