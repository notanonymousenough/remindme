from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..models.user import User
from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_telegram_id(self, telegram_id: str) -> User:
        """Получение пользователя по Telegram ID"""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_username(self, username: str) -> User:
        """Получение пользователя по имени пользователя"""
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_email(self, email: str) -> User:
        """Получение пользователя по email"""
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def update_last_active(self, user_id: UUID) -> User:
        """Обновление времени последней активности пользователя"""
        return await self.update(user_id, last_active=func.now())

    async def update_streak(self, user_id: UUID, streak: int) -> User:
        """Обновление серии пользователя"""
        return await self.update(user_id, streak=streak)

    async def add_experience(self, user_id: UUID, exp: int) -> User:
        """Добавление опыта пользователю с возможным повышением уровня"""
        user = await self.get(user_id)
        if not user:
            return None

        new_exp = user.experience + exp
        new_level = user.level

        # Простая формула для повышения уровня: 100 * текущий_уровень опыта
        exp_needed = 100 * user.level

        while new_exp >= exp_needed:
            new_exp -= exp_needed
            new_level += 1
            exp_needed = 100 * new_level

        return await self.update(user_id, experience=new_exp, level=new_level)
