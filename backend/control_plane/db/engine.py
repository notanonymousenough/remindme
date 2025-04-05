from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from backend.config import get_settings


class DatabaseEngine:
    @classmethod
    def create(cls, database_url: str, echo: bool = False, pool_size: int = 5,
                 max_overflow: int = 10, pool_timeout: int = 30, pool_recycle: int = 1800):
        engine = create_async_engine(
            database_url,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
        )

        async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
        return engine, async_session_maker


engine, async_session_maker = DatabaseEngine.create(get_settings().DATABASE_URI,
                                                    echo=get_settings().SQL_ECHO,
                                                    pool_size=get_settings().SQL_POOL_SIZE,
                                                    max_overflow=get_settings().SQL_MAX_OVERFLOW,
                                                    pool_timeout=get_settings().SQL_POOL_TIMEOUT,
                                                    pool_recycle=get_settings().SQL_POOL_RECYCLE)


async def get_async_session() -> AsyncSession:
    async with async_session_maker() as async_session:
        return async_session
