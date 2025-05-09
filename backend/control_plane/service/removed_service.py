from typing import Sequence
from uuid import UUID

from backend.control_plane.db.engine import get_async_session
from backend.control_plane.db.models import ReminderStatus
from backend.control_plane.db.repositories.habit import HabitRepository
from backend.control_plane.db.repositories.reminder import ReminderRepository
from backend.control_plane.schemas.requests.removed import RemovedEntities


class RemovedService:
    def __init__(self):
        self.reminders_repo = ReminderRepository()
        self.habits_repo = HabitRepository()

    async def get_removed_reminders_habits(self, user_id: UUID) -> RemovedEntities:
        need_statuses = [ReminderStatus.COMPLETED, ReminderStatus.FORGOTTEN]
        async with await get_async_session() as session:
            removed_reminders = await self.reminders_repo.get_removed(
                user_id,
                reminder_statuses=need_statuses,
                session=session
            )
            removed_habits = await self.habits_repo.get_models(
                user_id=user_id,
                session=session,
                **{"removed": True})

        return RemovedEntities.model_validate(
            {
                "habits": removed_habits,
                "reminders": removed_reminders
            }
        )

    async def restore_removed(self, reminder_id: UUID = None,
                              habit_id: UUID = None):
        async with await get_async_session() as session:
            if reminder_id:
                restored_reminder = await self.reminders_repo.update_model(reminder_id, session=session,
                                                                           **{"status": ReminderStatus.ACTIVE})
            if habit_id:
                restored_habit = await self.habits_repo.update_model(habit_id, session=session, **{"removed": False})
        if restored_reminder or restored_habit:
            return RemovedEntities.model_validate(
                {
                    "habit": restored_reminder,
                    "reminder": restored_habit
                }
            )
        return False


_removed_service = RemovedService()


def get_removed_service():
    return _removed_service
