"""
Активности для работы с нейроизображениями
"""
import logging
import json
from temporalio import activity
from typing import Dict, Any, Optional
from uuid import UUID

from app.db.engine import async_session
from app.db.repositories.habit import HabitRepository
from app.db.repositories.neuro_image import NeuroImageRepository
from app.db.models.base import ImageStatus
from ..services.yandex_gpt_service import YandexGPTService

logger = logging.getLogger("neuro_activities")


@activity.defn
async def generate_habit_image(
        habit_id: str,
        user_id: str,
        status: str,
        custom_prompt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Генерирует изображение для привычки с использованием ИИ
    """
    logger.info(f"Генерация изображения для привычки {habit_id}")

    async with async_session() as session:
        habit_repo = HabitRepository(session)
        neuro_image_repo = NeuroImageRepository(session)

        # Получаем привычку
        habit = await habit_repo.get(UUID(habit_id))
        if not habit:
            logger.warning(f"Привычка {habit_id} не найдена")
            return {"success": False, "error": "Привычка не найдена"}

        # Определяем статус для изображения
        image_status = ImageStatus.GOOD
        if status == "neutral":
            image_status = ImageStatus.NEUTRAL
        elif status == "bad":
            image_status = ImageStatus.BAD

        # Формируем промпт для генерации изображения
        if custom_prompt:
            prompt = custom_prompt
        else:
            # Формируем стандартный промпт на основе привычки и статуса
            if image_status == ImageStatus.GOOD:
                prompt = f"Яркое, позитивное изображение, показывающее успешное выполнение привычки: {habit.text}. Стиль: акварель, оптимистичный."
            elif image_status == ImageStatus.NEUTRAL:
                prompt = f"Нейтральное изображение, показывающее обычное выполнение привычки: {habit.text}. Стиль: фотореализм, повседневный."
            else:
                prompt = f"Тусклое, слегка негативное изображение, показывающее невыполнение привычки: {habit.text}. Стиль: темные тона, слегка грустное."

        # Генерируем изображение через ИИ
        yandex_gpt = YandexGPTService()
        image_result = await yandex_gpt.generate_image(prompt)

        if not image_result.get("success", False):
            logger.error(f"Ошибка генерации изображения: {json.dumps(image_result)}")
            return {"success": False, "error": "Ошибка генерации изображения"}

        # Сохраняем изображение в БД
        neuro_image = await neuro_image_repo.create(
            user_id=UUID(user_id),
            habit_id=UUID(habit_id),
            image_url=image_result["image_url"],
            thumbnail_url=image_result.get("thumbnail_url"),
            prompt=prompt,
            status=image_status
        )

        return {
            "success": True,
            "image_id": str(neuro_image.id),
            "image_url": neuro_image.image_url,
            "thumbnail_url": neuro_image.thumbnail_url,
            "prompt": prompt,
            "status": status
        }


@activity.defn
async def generate_achievement_image(
        achievement_id: str,
        user_id: str,
        achievement_name: str,
        achievement_description: str
) -> Dict[str, Any]:
    """
    Генерирует изображение для достижения с использованием ИИ
    """
    logger.info(f"Генерация изображения для достижения {achievement_id}")

    # Формируем промпт для генерации изображения
    prompt = f"Яркий, праздничный значок достижения для: {achievement_name} - {achievement_description}. " \
             f"Стиль: мультяшный, с золотым блеском, подходящий для игровой награды."

    # Генерируем изображение через ИИ
    yandex_gpt = YandexGPTService()
    image_result = await yandex_gpt.generate_image(prompt)

    if not image_result.get("success", False):
        logger.error(f"Ошибка генерации изображения достижения: {json.dumps(image_result)}")
        return {"success": False, "error": "Ошибка генерации изображения достижения"}

    return {
        "success": True,
        "image_url": image_result["image_url"],
        "thumbnail_url": image_result.get("thumbnail_url"),
        "prompt": prompt
    }
