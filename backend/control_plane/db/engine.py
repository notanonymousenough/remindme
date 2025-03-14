from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from backend.control_plane.config import get_settings


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


engine, async_session_maker = DatabaseEngine.create(get_settings().DATABASE_URI)


async def get_async_session() -> AsyncSession:
    async with async_session_maker() as async_session:
        return async_session
