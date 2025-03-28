import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from .engine import engine, Base, async_session
from .models.base import AchievementCategory
from .models.achievement import AchievementTemplate
import uuid

logger = logging.getLogger(__name__)


async def create_tables():
    """Создание таблиц в базе данных"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Таблицы созданы")


async def drop_tables():
    """Удаление всех таблиц из базы данных"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.info("Таблицы удалены")


async def seed_achievement_templates():
    """Наполнение таблицы шаблонов достижений"""
    async with async_session() as session:
        # Проверяем, нет ли уже шаблонов достижений
        from sqlalchemy.future import select

