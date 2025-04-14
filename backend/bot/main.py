import asyncio
import logging

from aiogram import Dispatcher

from backend.bot.app import bot
from backend.bot.clients.remindme_api import get_client_async
from backend.bot.middlewares.auth import AuthMiddleware
from backend.bot.middlewares.not_modified_messages import IgnoreMessageNotModifiedMiddleware
from routers import list_of_routers


def bind_routers(dispatcher: Dispatcher):
    for router in list_of_routers:
        dispatcher.include_router(router=router)


async def main():
    dp = Dispatcher()

    api_client = await get_client_async()

    bind_routers(dispatcher=dp)

    # middlewares registration
    auth_middleware = AuthMiddleware(api_client=api_client)
    dp.message.middleware.register(auth_middleware)
    dp.callback_query.middleware.register(auth_middleware)
    dp.callback_query.middleware(IgnoreMessageNotModifiedMiddleware())

    try:
        await dp.start_polling(bot)
    finally:
        # Закрываем ClientSession после завершения работы бота
        await api_client._close_session()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
