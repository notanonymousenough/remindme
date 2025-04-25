"""
Активности для работы с напоминаниями
"""
import logging
import asyncio
from datetime import datetime, timedelta
from temporalio import activity
from typing import List, Dict, Any
from uuid import UUID

from backend.control_plane.db.repositories.reminder import ReminderRepository
from backend.control_plane.db.repositories.user import UserRepository
from backend.control_plane.db.models.base import ReminderStatus
from backend.config import get_settings
from backend.data_plane.services.telegram_service import TelegramService

logger = logging.getLogger("reminder_activities")


@activity.defn
async def check_active_reminders() -> List[Dict[str, Any]]:
    """
    Проверяет напоминания, которые должны быть отправлены в ближайшее время
    """
    logger.info("Проверка активных напоминаний")
    reminder_repo = ReminderRepository()

    # Получаем активные напоминания в ближайшем временном окне
    active_reminders = await reminder_repo.take_for_sending(get_settings().ACTIVE_REMINDERS_LIMIT)

    # Формируем список напоминаний для отправки
    reminders_to_send = []
    for reminder in active_reminders:
        reminder_data = {
            "id": str(reminder.id),
            "user_id": str(reminder.user_id),
            "text": reminder.text,
            "time": reminder.time.isoformat()
        }
        reminders_to_send.append(reminder_data)

    return reminders_to_send

@activity.defn
async def send_telegram_notification(user_id: str, reminder_id: str, text: str, time: str):
    """
    Отправляет уведомление о напоминании через Telegram
    """
    logger.info(f"Отправка уведомления для напоминания {reminder_id}")

    reminder_time = datetime.fromisoformat(time)
    user_repo = UserRepository()
    user = await user_repo.get_by_model_id(UUID(user_id))

    # Формируем текст сообщения
    message = f"🔔 Напоминание: {text}\n⏰ Время: {reminder_time.strftime('%H:%M')}"

    # Добавляем кнопки для действий
    buttons = [
        [{"text": "✅ Выполнено", "callback_data": f"reminder_complete:{reminder_id}"}],
        [{"text": "⏰ Отложить на 15 минут", "callback_data": f"reminder_postpone:{reminder_id}:15"}],
        [{"text": "⏰ Отложить на 1 час", "callback_data": f"reminder_postpone:{reminder_id}:60"}]
    ]

    # Отправляем сообщение
    telegram_service = TelegramService()
    await telegram_service.send_message(
        user.telegram_id,
        message,
        reply_markup={"inline_keyboard": buttons}
    )

@activity.defn
async def abort_sent(reminder_id: str):
    """
    Выставляет напоминанию sent=False
    """
    logger.info(f"Отмена отправки напоминания {reminder_id}")

    reminder_repo = ReminderRepository()
    await reminder_repo.mark_sent(UUID(reminder_id), sent=False)
