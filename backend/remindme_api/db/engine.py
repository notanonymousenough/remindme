from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
import logging
from typing import AsyncGenerator

# Настройка логирования SQL запросов
logging.basicConfig()
logger = logging.getLogger("sqlalchemy.engine")
logger.setLevel(logging.INFO)

# Получение параметров подключения из переменных окружения
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/remind_me")

# Создание асинхронного движка SQLAlchemy
engine = create_async_engine(
    DATABASE_URL,
    echo=os.environ.get("SQL_ECHO", "False").lower() in ("true", "1", "t"),
    pool_size=int(os.environ.get("SQL_POOL_SIZE", "5")),
    max_overflow=int(os.environ.get("SQL_MAX_OVERFLOW", "10")),
    pool_timeout=int(os.environ.get("SQL_POOL_TIMEOUT", "30")),
    pool_recycle=int(os.environ.get("SQL_POOL_RECYCLE", "1800")),
)

# Создание сессии для работы с БД
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Базовый класс для моделей SQLAlchemy
Base = declarative_base()

# Функция-генератор для внедрения зависимостей в FastAPI
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
