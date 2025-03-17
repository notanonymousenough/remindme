import asyncio
import logging

from aiogram import Dispatcher, Bot

from routers import start_router, reminders_router, habits_router
from utils.config import get_settings


async def main():
    settings = get_settings()
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(reminders_router)
    dp.include_router(habits_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
