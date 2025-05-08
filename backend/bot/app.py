from aiogram import Bot

from backend.config import get_settings

bot = Bot(token=get_settings().BOT_TOKEN)
