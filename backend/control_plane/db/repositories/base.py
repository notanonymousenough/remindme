from typing import TypeVar, Generic, Type, List, Optional, Any, Dict, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, func
from uuid import UUID
from ..engine import Base

T = TypeVar('T', bound=Base)


class BaseRepository(Generic[T]):
    """
    Базовый класс репозитория с основными CRUD операциями
    """

    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model

    async def create(self, **kwargs) -> T:
        """Создание нового объекта"""
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def get(self, id: UUID) -> Optional[T]:
        """Получение объекта по ID"""
        stmt = select(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all(self) -> List[T]:
        """Получение всех объектов"""
        stmt = select(self.model)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def filter(self, **kwargs) -> List[T]:
        """Фильтрация объектов по указанным параметрам"""
        stmt = select(self.model)
        for key, value in kwargs.items():
            if value is not None:
                stmt = stmt.where(getattr(self.model, key) == value)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, id: UUID, **kwargs) -> Optional[T]:
        """Обновление объекта по ID"""
        stmt = update(self.model).where(self.model.id == id).values(**kwargs).returning(self.model)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalars().first()

    async def delete(self, id: UUID) -> bool:
        """Удаление объекта по ID"""
        stmt = delete(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0

    async def count(self, **kwargs) -> int:
        """Подсчет количества объектов с указанными параметрами"""
        stmt = select(func.count()).select_from(self.model)
        for key, value in kwargs.items():
            if value is not None:
                stmt = stmt.where(getattr(self.model, key) == value)
        result = await self.session.execute(stmt)
        return result.scalar_one()
