"""
Активности для работы с привычками
"""
import logging
import asyncio
from datetime import datetime, timedelta

from sqlalchemy.testing.suite.test_reflection import users
from temporalio import activity
from typing import List, Dict, Any
from uuid import UUID

from backend.control_plane.db.repositories.reminder import ReminderRepository
from backend.control_plane.db.repositories.user import UserRepository
from backend.control_plane.db.models.base import ReminderStatus
from backend.config import get_settings
from backend.data_plane.services.telegram_service import TelegramService

logger = logging.getLogger("morning_message_activities")


@activity.defn
async def get_active_users() -> List[str]:
    logger.info("Получение списка пользователей")
    user_repo = UserRepository()
    users = await user_repo.get_all_models()
    return list(map(lambda user: user.id, users))


@activity.defn
async def check_today_habits(user_id: str) -> List[Dict[str, Any]]:
    """
    Проверяет напоминания, которые должны быть отправлены в ближайшее время
    """
    logger.info("Проверка активных привычек")
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

        # Помечаем, что уведомление было отправлено
        await reminder_repo.mark_sent(reminder.id)

    return reminders_to_send


@activity.defn
async def check_today_reminders(user_id: str) -> List[Dict[str, Any]]:
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

        # Помечаем, что уведомление было отправлено
        await reminder_repo.mark_sent(reminder.id)

    return reminders_to_send

@activity.defn
async def send_telegram_message(user_id: str, habit_id: str, text: str, time: str):
    """
    Отправляет уведомление о напоминании через Telegram
    """
    logger.info(f"Отправка утреннего уведомления для пользователя {user_id}")

    reminder_time = datetime.fromisoformat(time)
    user_repo = UserRepository()
    user = await user_repo.get_by_model_id(UUID(user_id))

    # Формируем текст сообщения
    message = f"🔔 Напоминание: {text}\n⏰ Время: {reminder_time.strftime('%H:%M')}"

    # Отправляем сообщение
    telegram_service = TelegramService()
    await telegram_service.send_message(
        user.telegram_id,
        message
    )
