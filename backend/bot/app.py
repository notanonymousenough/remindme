from aiogram import Bot

from utils.config import get_settings

settings = get_settings()
bot = Bot(token=settings.BOT_TOKEN)
