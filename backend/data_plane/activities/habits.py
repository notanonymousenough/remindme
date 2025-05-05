"""
Активности для работы с привычками
"""
import logging
import asyncio
from datetime import datetime, timedelta
from itertools import count

from temporalio import activity
from typing import List, Dict, Any, Tuple, Sequence
from uuid import UUID

from backend.control_plane.ai_clients import prompts, default_art_ai_provider, default_llm_ai_provider
from backend.control_plane.ai_clients.prompts import RequestType
from backend.control_plane.db.models import ImageStatus, HabitInterval, Habit
from backend.control_plane.db.repositories.habit import HabitRepository
from backend.control_plane.db.repositories.neuro_image import NeuroImageRepository
from backend.control_plane.db.repositories.reminder import ReminderRepository
from backend.control_plane.db.repositories.user import UserRepository
from backend.control_plane.db.models.base import ReminderStatus
from backend.config import get_settings
from backend.control_plane.exceptions.quota import QuotaExceededException
from backend.control_plane.schemas.habit import HabitSchemaResponse
from backend.control_plane.service.quota_service import QuotaService
from backend.control_plane.utils import timeutils
from backend.data_plane.services.s3_service import YandexStorageService
from backend.data_plane.services.telegram_service import TelegramService

logger = logging.getLogger("reminder_activities")

art_ai_provider = default_art_ai_provider

@activity.defn
async def check_active_habits() -> Sequence[dict]:
    logger.info("Проверка активных привычек")
    habits_repo = HabitRepository()
    # Получаем активные привычки
    habits = await habits_repo.take_for_image_generation()
    return [habit.model_dump(exclude={"start_date", "end_date", "created_at", "updated_at", "progress"}) for habit in habits]

@activity.defn
async def update_illustrate_habit_quota(user_id: UUID) -> bool:
    quota_service = QuotaService()
    try:
        await quota_service.check_and_increment_ai_art_usage(user_id, RequestType.ILLUSTRATE_HABIT)
        return True
    except QuotaExceededException:
        return False


@activity.defn
async def get_habit_completion_rate(habit_id: UUID, interval: HabitInterval) -> float:
    habits_repo = HabitRepository()

    today = timeutils.get_utc_now().date()
    period_start = today - timedelta(weeks=4) # месяц
    if interval == HabitInterval.WEEKLY:
        period_start = today - timedelta(weeks=6*4) # полгода
    elif interval == HabitInterval.MONTHLY:
        period_start = today - timedelta(weeks=12*4) # год

    progress = await habits_repo.get_progress_for_period(habit_id, period_start, today)

    # Расчет прогресса
    if interval == HabitInterval.DAILY:
        expected = (today - period_start).days + 1
        done = sum(1 for d in progress if period_start <= d.record_date.python_value <= today)
    elif interval == HabitInterval.WEEKLY:
        week_starts = [period_start + timedelta(days=i) for i in range(0, (today - period_start).days + 1) if
                       (period_start + timedelta(days=i)).weekday() == 0]
        expected = len(week_starts)
        done = sum(1 for d in progress if period_start <= d.record_date.python_value <= today)
    else:
        month_starts = [period_start + timedelta(days=i) for i in range(0, (today - period_start).days + 1) if
                       (period_start + timedelta(days=i)).day == 1]
        expected = len(month_starts)
        done = sum(1 for d in progress if period_start <= d.record_date.python_value <= today)

    completion_rate = done / expected if expected else 0

    return completion_rate

@activity.defn
async def generate_and_save_image(user_id: UUID, habit_text: str, completion_rate: float) -> Tuple[str, int]:
    """
    Генерирует изображение и сразу сохраняет его в S3
    """
    character = get_settings().HABIT_IMAGE_CHARACTER
    seed = int(datetime.now().timestamp())
    im_bytes, count_tokens = await art_ai_provider.generate_habit_image(
        character, habit_text, completion_rate, seed=seed
    )

    # Сразу сохраняем в S3
    s3_service = YandexStorageService()
    image_url = s3_service.save_image(bytearray(im_bytes), f"habit_images/{user_id}")

    return image_url, count_tokens

@activity.defn
async def update_describe_habit_text_quota(user_id: UUID, count_tokes: int):
    quota_service = QuotaService()
    await quota_service.update_ai_llm_request_usage(user_id, RequestType.DESCRIBE_HABIT_TEXT, count_tokes, custom_ai_provider=art_ai_provider)

@activity.defn
async def save_image_to_db(user_id: UUID, habit_id: UUID, image_url: str):
    images_repo = NeuroImageRepository()
    await images_repo.create(user_id, habit_id=habit_id, image_url=image_url, status=ImageStatus.GENERATED)
