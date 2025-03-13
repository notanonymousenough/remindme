"""
Активности для работы с календарем
"""
import logging
from datetime import datetime, timedelta
from temporalio import activity
from typing import List, Dict, Any
from uuid import UUID

from app.db.engine import async_session
from app.db.repositories.user import UserRepository
from app.db.repositories.reminder import ReminderRepository
from ..services.caldav_service import CalDAVService

logger = logging.getLogger("calendar_activities")


@activity.defn
async def sync_calendar_events(user_id: str) -> Dict[str, Any]:
    """
    Синхронизирует напоминания пользователя с его календарем
    """
    logger.info(f"Синхронизация календаря для пользователя {user_id}")

    async with async_session() as session:
        user_repo = UserRepository(session)
        reminder_repo = ReminderRepository(session)

        # Получаем пользователя
        user = await user_repo.get(UUID(user_id))
        if not user or not user.calendar_integration_key:
            logger.warning(f"Пользователь {user_id} не найден или не имеет ключа интеграции с календарем")
            return {"success": False, "error": "Интеграция с календарем не настроена"}

        # Получаем активные напоминания пользователя
        now = datetime.now()
        sync_window = now + timedelta(days=30)  # Синхронизируем на 30 дней вперед

        active_reminders = await reminder_repo.get_reminders_in_time_window(
            user_id=UUID(user_id),
            start_time=now,
            end_time=sync_window
        )

        # Создаем сервис интеграции с календарем
        caldav_service = CalDAVService(user.calendar_integration_key)

        # Синхронизируем напоминания с календарем
        synced_events = await caldav_service.sync_reminders(active_reminders)

        return {
            "success": True,
            "synced_count": len(synced_events),
            "total_reminders": len(active_reminders)
        }
