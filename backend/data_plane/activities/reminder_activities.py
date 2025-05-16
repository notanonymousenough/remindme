"""
Активности для работы с напоминаниями
"""
import logging
import asyncio
from datetime import datetime, timedelta
from temporalio import activity
from typing import List, Dict, Any
from uuid import UUID

from app.db.engine import async_session
from app.db.repositories.reminder import ReminderRepository
from app.db.repositories.user import UserRepository
from app.db.models.base import ReminderStatus
from ..services.telegram_service import TelegramService

logger = logging.getLogger("reminder_activities")


@activity.defn
async def check_active_reminders() -> List[Dict[str, Any]]:
    """
    Проверяет напоминания, которые должны быть отправлены в ближайшее время
    """
    logger.info("Проверка активных напоминаний")

    now = datetime.now()
    reminder_window = now + timedelta(minutes=5)  # Смотрим напоминания на ближайшие 5 минут

    async with async_session() as session:
        # Создаем репозиторий напоминаний
        reminder_repo = ReminderRepository(session)

        # Получаем активные напоминания в ближайшем временном окне
        active_reminders = await reminder_repo.get_reminders_in_time_window(
            start_time=now,
            end_time=reminder_window,
            status=ReminderStatus.ACTIVE,
            notification_sent=False
        )

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

            # Помечаем, что уведомление было отправлено
            await reminder_repo.update(reminder.id, notification_sent=True)

        return reminders_to_send


@activity.defn
async def mark_reminder_as_forgotten(reminder_id: str) -> bool:
    """
    Отмечает напоминание как забытое
    """
    logger.info(f"Отметка напоминания {reminder_id} как забытое")

    async with async_session() as session:
        reminder_repo = ReminderRepository(session)
        result = await reminder_repo.mark_as_forgotten(UUID(reminder_id))
        return result is not None


@activity.defn
async def send_telegram_notification(user_id: str, reminder_id: str, text: str, time: str) -> bool:
    """
    Отправляет уведомление о напоминании через Telegram
    """
    logger.info(f"Отправка уведомления для напоминания {reminder_id}")

    reminder_time = datetime.fromisoformat(time)

    async with async_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get(UUID(user_id))

        if not user or not user.telegram_id:
            logger.warning(f"Пользователь {user_id} не найден или не имеет привязки к Telegram")
            return False

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
        success = await telegram_service.send_message(
            user.telegram_id,
            message,
            reply_markup={"inline_keyboard": buttons}
        )

        return success
