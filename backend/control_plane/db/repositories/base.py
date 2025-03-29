from datetime import datetime
from typing import TypeVar, Generic, Type, List, Optional, Any, Dict, Union

import jwt
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy import update, delete, func, and_, all_
from uuid import UUID
from ..engine import Base, get_async_session
from ...config import get_settings

T = TypeVar('T', bound=Base)


class BaseRepository(Generic[T]):
    """
    Базовый класс репозитория с основными CRUD операциями
    """

    def __init__(self, model: Type[T]):
        self.model = model

    async def create(self, token: str = Depends(get_settings().OAUTH2_SCHEME), **kwargs) -> T:
        async with await get_async_session() as session:
            decoded_jwt = jwt.decode(token, get_settings().SECRET_KEY, algorithms=[get_settings().ALGORITHM])
            user_id = decoded_jwt.get("user_id")

            obj = self.model(**kwargs)
            obj.user_id = user_id
            session.add(obj)

            await session.flush()
            await session.commit()
            return obj

    async def get_by_model_id(self, model_id: UUID, token: str = Depends(get_settings().OAUTH2_SCHEME)) -> Optional[T]:
        async with await get_async_session() as session:
            decoded_jwt = jwt.decode(token, get_settings().SECRET_KEY, algorithms=[get_settings().ALGORITHM])
            user_id = decoded_jwt.get("user_id")

            stmt = select(self.model).where(
                and_(
                    getattr(self.model, "user_id") == user_id,
                    getattr(self.model, "id") == model_id
                ).returning(self.model)
            )
            result = await session.execute(stmt)
            return result.scalars().one_or_none()

    async def get_models(self, token: str = Depends(get_settings().OAUTH2_SCHEME), **kwargs) -> Optional[T]:
        async with await get_async_session() as session:
            decoded_jwt = jwt.decode(token, get_settings().SECRET_KEY, algorithms=[get_settings().ALGORITHM])
            user_id = decoded_jwt.get("user_id")

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

    async def update_model(self, model_id: UUID, token: str = Depends(get_settings().OAUTH2_SCHEME), **kwargs) -> Optional[T]:
        async with await get_async_session() as session:
            decoded_jwt = jwt.decode(token, get_settings().SECRET_KEY, algorithms=[get_settings().ALGORITHM])
            user_id = decoded_jwt.get("user_id")

            stmt = update(self.model).where(
                and_(
                    getattr(self.model, "user_id") == user_id,
                    getattr(self.model, "id") == model_id
                )
            ).values(**kwargs).returning(self.model)
            result = await session.execute(stmt)
            await session.flush()
            return result.scalars().first()

    async def delete_model(self, model_id: UUID, token: str = Depends(get_settings().OAUTH2_SCHEME)) -> bool:
        async with await get_async_session() as session:
            decoded_jwt = jwt.decode(token, get_settings().SECRET_KEY, algorithms=[get_settings().ALGORITHM])
            user_id = decoded_jwt.get("user_id")

            stmt = delete(self.model).where(
                and_(
                    getattr(self.model, "user_id") == user_id,
                    getattr(self.model, "id") == model_id
                )
            )
            result = await session.execute(stmt)
            await session.flush()
            return result.rowcount() > 0

    async def count_models(self, token: str = Depends(get_settings().OAUTH2_SCHEME), **kwargs) -> int:
        async with await get_async_session() as session:
            decoded_jwt = jwt.decode(token, get_settings().SECRET_KEY, algorithms=[get_settings().ALGORITHM])
            user_id = decoded_jwt.get("user_id")

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
