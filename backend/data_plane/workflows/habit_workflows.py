"""
Рабочие процессы для обработки привычек
"""
import logging
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from typing import List, Dict, Any, Optional

with workflow.unsafe.imports_passed_through():
    from ..activities.habit_activities import (
        update_habit_streaks,
        process_habit_progress
    )
    from ..activities.neuro_activities import generate_habit_image
    import logging

logger = logging.getLogger("habit_workflows")


@workflow.defn
class ProcessHabitsWorkflow:
    """
    Рабочий процесс для обработки привычек
    """

    @workflow.run
    async def run(self) -> Dict[str, Any]:
        # Настраиваем политику повторных попыток для активностей
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(minutes=10),
            maximum_attempts=3
        )

        # Обновляем серии привычек
        processed_count = await workflow.execute_activity(
            update_habit_streaks,
            retry_policy=retry_policy,
            start_to_close_timeout=timedelta(minutes=10)
        )

        return {
            "processed_habits_count": processed_count
        }


@workflow.defn
class GenerateHabitImageWorkflow:
    """
    Рабочий процесс для генерации изображения привычки
    """

    @workflow.run
    async def run(
            self,
            habit_id: str,
            user_id: str,
            status: str,
            custom_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        # Настраиваем политику повторных попыток для активностей
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(minutes=5),
            maximum_attempts=2,  # Меньше попыток для генерации изображений
            non_retryable_error_types=["ValueError", "KeyError"]
        )

        # Генерируем изображение
        result = await workflow.execute_activity(
            generate_habit_image,
            retry_policy=retry_policy,
            start_to_close_timeout=timedelta(minutes=5),
            args=[habit_id, user_id, status, custom_prompt]
        )

        return result
