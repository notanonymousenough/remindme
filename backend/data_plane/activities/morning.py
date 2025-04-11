"""
Активности для работы с привычками
"""
import logging
import asyncio
from datetime import datetime, timedelta
from pyexpat.errors import messages

from temporalio import activity
from typing import List, Dict, Any
from uuid import UUID

from backend.control_plane.db.repositories.habit import HabitRepository
from backend.control_plane.db.repositories.reminder import ReminderRepository
from backend.control_plane.db.repositories.user import UserRepository
from backend.control_plane.db.models.base import ReminderStatus
from backend.config import get_settings
from backend.data_plane.services.telegram_service import TelegramService

logger = logging.getLogger("morning_message_activities")


@activity.defn
async def get_active_users() -> List[UUID]:
    logger.info("Получение списка пользователей")
    user_repo = UserRepository()
    users = await user_repo.get_all_models()
    return list(map(lambda user: user.id, users))


@activity.defn
async def check_today_habits(user_id: UUID) -> List[Dict[str, Any]]:
    """
    Проверяет привычки, которые должны быть выполнены сегодня
    """
    logger.info("Проверка активных привычек")
    # habits_repo = HabitRepository()
    #
    # # Получаем активные напоминания в ближайшем временном окне
    # active_reminders = await habits_repo.get_active_habits(user_id=user_id)
    #
    # # Формируем список напоминаний для отправки
    # reminders_to_send = []
    # for reminder in active_reminders:
    #     reminder_data = {
    #         "id": str(reminder.id),
    #         "user_id": str(reminder.user_id),
    #         "text": reminder.text,
    #         "time": reminder.time.isoformat()
    #     }
    #     reminders_to_send.append(reminder_data)
    #
    # return reminders_to_send
    return []


@activity.defn
async def check_today_reminders(user_id: UUID) -> List[Dict[str, Any]]:
    """
    Проверяет напоминания, которые должны быть отправлены сегодня
    """
    logger.info("Проверка активных напоминаний")
    reminder_repo = ReminderRepository()

    # Получаем активные напоминания в ближайшем временном окне
    active_reminders = await reminder_repo.get_active_reminders(user_id=user_id)

    # Формируем список напоминаний для отправки
    reminders_to_send = []
    for reminder in active_reminders:
        if reminder.time.date() != datetime.now().date():
            continue
        reminder_data = {
            "id": str(reminder.id),
            "user_id": str(reminder.user_id),
            "text": reminder.text,
            "time": reminder.time.isoformat()
        }
        reminders_to_send.append(reminder_data)

    return reminders_to_send

@activity.defn
async def send_telegram_message(user_id: str, reminders: List[Dict[str, Any]], habits: List[Dict[str, Any]]):
    """
    Отправляет сообщение через Telegram
    """
    logger.info(f"Отправка утреннего уведомления для пользователя {user_id}")

    user_repo = UserRepository()
    user = await user_repo.get_by_model_id(UUID(user_id))

    # Формируем текст сообщения
    reminders_string = ""
    habits_string = ""
    if len(reminders):
        reminders_string = "🎯 Задачи на сегодня:"
        for reminder in reminders:
            # TODO: зачеркивать если выполнено
            reminders_string += f"{reminder["text"]}\n"
    if len(habits):
        if len(reminders):
            habits_string = "🧩 Привычки:\n"
        else:
            habits_string = "🧩 Привычки на сегодня:\n"
        for habit in habits:
            habits_string += f"{habit["text"]}\n"
    message = f"{reminders_string}\n{habits_string}\nХорошего и продуктивного дня! ✨"

    # Отправляем сообщение
    telegram_service = TelegramService()
    await telegram_service.send_message(
        user.telegram_id,
        message
    )
