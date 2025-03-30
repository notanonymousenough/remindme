from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import os
import logging

from backend.control_plane.config import get_settings

# Настройка логирования SQL запросов
logging.basicConfig()
logger = logging.getLogger("sqlalchemy.engine")
logger.setLevel(logging.INFO)

# Получение параметров подключения из переменных окружения
load_dotenv()
DATABASE_URL = get_settings().DATABASE_URI

# Создание асинхронного движка SQLAlchemy
engine = create_async_engine(
    DATABASE_URL,
    echo=os.environ.get("SQL_ECHO", "False").lower() in ("true", "1", "t"),
    pool_size=int(os.environ.get("SQL_POOL_SIZE", "5")),
    max_overflow=int(os.environ.get("SQL_MAX_OVERFLOW", "10")),
    pool_timeout=int(os.environ.get("SQL_POOL_TIMEOUT", "30")),
    pool_recycle=int(os.environ.get("SQL_POOL_RECYCLE", "1800")),
)

async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session() -> AsyncSession:
    async with async_session_maker() as async_session:  # every time we get new session
        return async_session
