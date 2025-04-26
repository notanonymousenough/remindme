"""
Активности для работы с привычками
"""
import logging
import asyncio
from datetime import datetime, timedelta
from itertools import count

from temporalio import activity
from typing import List, Dict, Any, Tuple
from uuid import UUID

from backend.control_plane.ai_clients import prompts, default_art_ai_provider, default_llm_ai_provider
from backend.control_plane.ai_clients.prompts import RequestType
from backend.control_plane.db.models import ImageStatus
from backend.control_plane.db.repositories.habit import HabitRepository, HabitProgressRepository
from backend.control_plane.db.repositories.neuro_image import NeuroImageRepository
from backend.control_plane.db.repositories.reminder import ReminderRepository
from backend.control_plane.db.repositories.user import UserRepository
from backend.control_plane.db.models.base import ReminderStatus
from backend.config import get_settings
from backend.control_plane.service.quota_service import QuotaService
from backend.data_plane.services.s3_service import YandexStorageService
from backend.data_plane.services.telegram_service import TelegramService

logger = logging.getLogger("reminder_activities")

MIN_DAYS_FOR_GENERATING = timedelta(days=14)
art_ai_provider = default_art_ai_provider

@activity.defn
async def check_active_habits() -> List[Dict[str, Any]]:
    """
    Проверяет напоминания, которые должны быть отправлены в ближайшее время
    """
    logger.info("Проверка активных привычек")
    habits_repo = HabitRepository()
    habits_progress_repo = HabitProgressRepository()
    images_repo = NeuroImageRepository()
    quota_service = QuotaService()

    # Получаем активные привычки
    habits = await habits_repo.take_for_image_generation(get_settings().GENERATE_IMAGES_LIMIT)

    # Формируем список изображений
    images_to_generate = []
    for habit in habits:
        today = datetime.now().date()
        month_start = today.replace(day=1)
        if month_start - today < MIN_DAYS_FOR_GENERATING:
            month_start = today - MIN_DAYS_FOR_GENERATING
        progress = await habits_progress_repo.get_progress_for_period(habit.id, month_start, today)
        await quota_service.check_and_increment_ai_art_usage(habit.user_id, RequestType.ILLUSTRATE_HABIT)
        image = await images_repo.create(habit.user_id, habit_id=habit.id, status=ImageStatus.GENERATING)
        images_to_generate.append({
            "progress": progress,
            "image": image,
            "habit": habit
        })

    return images_to_generate

@activity.defn
async def generate_image(image: dict) -> Tuple[bytes, int]:
    """
    Генерирует изображение для привычки
    """
    logger.info(f"Генерация изображения {image}")
    im_bytes, count_tokens = art_ai_provider.generate_habit_image(image['habit'].text, image['progress'], image['habit'].interval)
    return im_bytes, count_tokens


@activity.defn
async def update_quota(user_id: UUID, count_tokes: int):
    quota_service = QuotaService()
    await quota_service.update_ai_llm_request_usage(user_id, RequestType.DESCRIBE_HABIT_TEXT, count_tokes, custom_ai_provider=art_ai_provider)


@activity.defn
async def save_image_to_s3(image_bytes: bytes) -> str:
    s3_service = YandexStorageService()
    return s3_service.save_image(bytearray(image_bytes), "habit_images")

@activity.defn
async def save_image_url_to_db(image, image_url):
    images_repo = NeuroImageRepository()
    await images_repo.update_model(image['image'].id, image_url=image_url)
