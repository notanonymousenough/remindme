import asyncio
import logging

from aiogram import Dispatcher

from backend.bot.app import bot
from routers import start_router, reminders_router, habits_router


async def main():
    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(reminders_router)
    dp.include_router(habits_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
