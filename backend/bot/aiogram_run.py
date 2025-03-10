import asyncio

from handlers.reminders import reminder_route
from create_bot import bot, dp
from handlers.start import start_route


async def main():
    dp.include_router(start_route)
    dp.include_router(reminder_route)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
