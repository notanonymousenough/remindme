import asyncio
from create_bot import bot, dp
from handlers.start import start_router
from handlers.habits import habit_router


async def main():
    dp.include_router(start_router)
    dp.include_router(habit_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
