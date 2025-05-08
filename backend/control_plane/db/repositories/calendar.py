from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, func
from datetime import date, timedelta
from typing import List, Optional, Dict, Sequence
from uuid import UUID

from backend.control_plane.db.engine import get_async_session
from backend.control_plane.db.models.calendar import CalendarIntegration
from backend.control_plane.db.repositories.base import BaseRepository


class CalendarIntegrationRepository(BaseRepository[CalendarIntegration]):
    def __init__(self):
        super().__init__(CalendarIntegration)

    async def get_active_by_user(self, user_id: UUID) -> List[CalendarIntegration]:
        async with get_async_session() as session:
            stmt = select(CalendarIntegration).where(
                and_(
                    CalendarIntegration.user_id == user_id,
                    CalendarIntegration.active == True,
                )
            )
            result = await session.execute(stmt)
            return result.scalars().all()
