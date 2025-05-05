from aiogram import Bot

from utils import get_settings


settings = get_settings()
bot = Bot(token=settings.BOT_TOKEN)
