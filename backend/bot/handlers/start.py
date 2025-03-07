from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import Message, CallbackQuery

from backend.bot.keyboards import reply_kbs, inline_kbs

start_router = Router()


@start_router.message(CommandStart())
async def start_menu(message: Message):
    await message.answer(text="Нажмите кнопку :)", reply_markup=kbs.main_menu())


@start_router.message(F.text == "Напоминания")
async def reminders_menu(message: Message):
    temp = ("Ваши напоминания: \n\nСегодня:\n1) Погладить одеяло \n\n "
            "Выберите напоминание для редактирования:")
    await message.answer(text=temp, reply_markup=kbs.reminders_menu())



@start_router.message(F.text == "Назад")
async def start_menu(message: Message):
    await message.answer(text="Возращение в главное меню", reply_markup=kbs.main_menu())

