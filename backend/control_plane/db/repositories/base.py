from datetime import datetime
from typing import TypeVar, Generic, Type, List, Optional, Any, Dict, Union

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy import update, delete, func
from uuid import UUID
from ..engine import Base, get_async_session

T = TypeVar('T', bound=Base)


class BaseRepository(Generic[T]):
    """
    Базовый класс репозитория с основными CRUD операциями
    """

    def __init__(self, model: Type[T]):
        self.model = model

    async def create(self, **kwargs) -> T:
        async with await get_async_session() as session:
            obj = self.model(**kwargs)
            session.add(obj)
            await session.flush()
            await session.commit()
            return obj

    async def get(self, id: UUID) -> Optional[T]:
        async with await get_async_session() as session:
            stmt = select(self.model).where(self.model.id == id)
            result = await session.execute(stmt)
            return result.scalars().one()

    async def get_all(self) -> Optional[T]:
        async with await get_async_session() as session:
            stmt = select(self.model)
            result = await session.execute(stmt)
            return result.scalars().all()

    async def filter(self, **kwargs) -> List[T]:
        async with await get_async_session() as session:
            """Фильтрация объектов по указанным параметрам"""
            stmt = select(self.model)
            for key, value in kwargs.items():
                if value is not None:
                    stmt = stmt.where(getattr(self.model, key) == value)
            result = await session.execute(stmt)
            return result.scalars().all()

    async def update(self, id: UUID, **kwargs) -> Optional[T]:
        async with await get_async_session() as session:
            """Обновление объекта по ID"""
            stmt = update(self.model).where(self.model.id == id).values(**kwargs).returning(self.model)
            result = await session.execute(stmt)
            await session.flush()
            return result.scalars().first()

    async def delete(self, id: UUID) -> bool:
        async with await get_async_session() as session:
            """Удаление объекта по ID"""
            stmt = delete(self.model).where(self.model.id == id)
            result = await session.execute(stmt)
            await session.flush()
            return result.rowcount() > 0

    async def count(self, **kwargs) -> int:
        async with await get_async_session() as session:
            """Подсчет количества объектов с указанными параметрами"""
            stmt = select(func.count()).select_from(self.model)
            for key, value in kwargs.items():
                if value is not None:
                    stmt = stmt.where(getattr(self.model, key) == value)
            result = await session.execute(stmt)
            return result.scalar_one()
