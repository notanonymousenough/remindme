from typing import TypeVar, Generic, Type, Optional, Sequence

from fastapi import HTTPException
from sqlalchemy.future import select
from sqlalchemy import update, delete, func, and_
from uuid import UUID
from ..engine import get_async_session
from ..models import BaseModel

T = TypeVar('T', bound=BaseModel)


class BaseRepository(Generic[T]):
    """
    Базовый класс репозитория с основными CRUD операциями
    """

    def __init__(self, model: Type[T]):
        self.model = model

    async def create(self, user_id: UUID, **kwargs) -> T:
        async with await get_async_session() as session:
            obj = self.model(**kwargs)
            obj.user_id = user_id
            session.add(obj)

            await session.flush()
            await session.commit()
            return obj

    async def get_by_model_id(self, model_id: UUID) -> Optional[T]:
        async with await get_async_session() as session:
            stmt = select(self.model).where(
                and_(
                    getattr(self.model, "id") == model_id
                ).returning(self.model)
            )
            result = await session.execute(stmt)
            return result.scalars().one_or_none()

    async def get_models(self, user_id: UUID, **kwargs) -> Sequence[T]:
        async with await get_async_session() as session:
            stmt = select(self.model).where(
                and_(
                    getattr(self.model, "user_id") == user_id
                )
            )
            for key, value in kwargs.items():
                stmt = stmt.where(
                    and_(
                        getattr(self.model, key) == value
                    )
                )
            result = await session.execute(stmt)
            return result.scalars().all()

    async def update_model(self, model_id: UUID, **kwargs) -> Optional[T]:
        async with await get_async_session() as session:
            stmt = update(self.model).where(
                and_(
                    getattr(self.model, "id") == model_id
                )
            ).values(**kwargs).returning(self.model)
            result = await session.execute(stmt)
            await session.commit()
            return result.scalars().first()

    async def delete_model(self, user_id: UUID, model_id: UUID) -> bool:
        async with await get_async_session() as session:
            try:
                count_models = await self.count_models(user_id=user_id)
                stmt = delete(self.model).where(
                    and_(
                        getattr(self.model, "id") == model_id
                    )
                )
                await session.execute(stmt)
                await session.commit()
                return True if count_models - await self.count_models(user_id=user_id) else False
            except Exception as ex:
                raise HTTPException(404, detail=f"Exception: {ex}")

    async def count_models(self, user_id: UUID, **kwargs) -> int:
        async with await get_async_session() as session:
            stmt = select(func.count()).select_from(self.model).where(
                and_(
                    getattr(self.model, "user_id") == user_id
                )
            )
            for key, value in kwargs.items():
                if value is not None:
                    stmt = stmt.where(
                        and_(
                            getattr(self.model, key) == value
                        )
                    )
            result = await session.execute(stmt)
            return result.scalar_one()
