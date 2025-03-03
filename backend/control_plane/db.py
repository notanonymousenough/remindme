from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.control_plane.config import get_settings
from backend.control_plane.models.base import BaseTable


class SessionManager:
    """
    A class that implements the necessary functionality for working with the database:
    issuing sessions, storing and updating connection settings.
    """

    def __init__(self) -> None:
        self.refresh()

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(SessionManager, cls).__new__(cls)
        return cls.instance  # noqa

    def get_session_maker(self) -> sessionmaker:
        return sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

    def refresh(self) -> None:
        self.engine = create_async_engine(get_settings().database_uri, echo=True, future=True)



async def get_session() -> AsyncSession:
    session_maker = SessionManager().get_session_maker()
    async with session_maker() as session:
        yield session


async def init_models():
    async with SessionManager().engine.begin() as conn:
        await conn.run_sync(BaseTable.metadata.drop_all)
        await conn.run_sync(BaseTable.metadata.create_all)


__all__ = [
    "get_session",
]
