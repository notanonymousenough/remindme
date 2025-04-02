import asyncio
import logging
from aiogram import Dispatcher

from backend.bot.app import bot
from backend.bot.clients.remindme_api import get_client_async
from backend.bot.middlewares.auth import AuthMiddleware
from backend.bot.middlewares.not_modified_messages import IgnoreMessageNotModifiedMiddleware
from routers import start_router, reminders_router, habits_router


async def main():
    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(reminders_router)
    dp.include_router(habits_router)

    api_client = await get_client_async()
    auth_middleware = AuthMiddleware(api_client=api_client)

    dp.message.middleware.register(auth_middleware)
    dp.callback_query.middleware.register(auth_middleware)  # Если нужно для callback_query тоже

    dp.callback_query.middleware(IgnoreMessageNotModifiedMiddleware())

    try:
        await dp.start_polling(bot)
    finally:
        # Закрываем ClientSession после завершения работы бота
        await api_client._close_session()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
