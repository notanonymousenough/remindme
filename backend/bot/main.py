import asyncio
import logging

from aiogram import Dispatcher

from backend.bot.app import bot
from backend.bot.middlewares.not_modified_messages import IgnoreMessageNotModifiedMiddleware
from backend.config import get_settings
from backend.bot.routers.reminder_state_actions.edit_reminder import edit_reminder_router
from backend.bot.routers.reminder_state_actions.new_reminder import add_reminder_router
from backend.bot.routers.tags import tags_router
from routers import start_router, reminders_router, habits_router


async def main():
    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(reminders_router)
    dp.include_router(habits_router)

    dp.callback_query.middleware(IgnoreMessageNotModifiedMiddleware())

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=get_settings().LOG_LEVEL)
    asyncio.run(main())
