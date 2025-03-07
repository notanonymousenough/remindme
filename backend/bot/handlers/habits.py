from aiogram import Router, F
from aiogram.filters.callback_data import CallbackData
from aiogram.types import Message

from backend.bot.keyboards import inline_kbs, reply_kbs

habit_router = Router()


@habit_router.message(F.text == "Привычки")
async def menu(message: Message):
    temp = "Ваши привычки: \n\n1) Отжимания (6/30) ❌\n2) Кормить кота (7/30) ✅"
    await message.answer(text=temp, reply_markup=inline_kbs.reminders_buttons(20, "today"))
    await message.answer(text="..", reply_markup=kbs.habits_menu())


@habit_router.callback_query(F.data.startswith("reminder_next"))
async def menu_next(call: CallbackData):
    next_count = int(call.dict()["data"].split("_")[-1])
    temp = "Ваши привычки: \n\n3) Отжимания (6/30) ❌\n4) Кормить кота (7/30) ✅"
    await call.message.answer(text=temp, reply_markup=inline_kbs.reminders_buttons(20, "today", next_count))
