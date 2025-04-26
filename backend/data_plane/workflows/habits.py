"""
Рабочие процессы для обработки привычек
"""
import asyncio
import logging
from datetime import timedelta
from uuid import UUID

from falcon.response import datetime
from temporalio import workflow
from temporalio.common import RetryPolicy
from typing import List, Dict, Any

from temporalio.exceptions import ActivityError
from temporalio.workflow import ParentClosePolicy

from backend.config import get_settings
from backend.control_plane.exceptions.quota import QuotaExceededException

with workflow.unsafe.imports_passed_through():
    from backend.data_plane.activities.habits import (
        check_active_habits,
        generate_image,
        save_image_to_s3,
        save_image_to_db,
        update_describe_habit_text_quota,
        get_habit_completion_rate,
        update_illustrate_habit_quota
)
    import logging

logger = logging.getLogger("habit_workflows")


@workflow.defn
class StartImagesGenerationWorkflow:
    """
    Рабочий процесс для инициализации генерации изображений
    """

    @workflow.run
    async def run(self):
        # Настраиваем политику повторных попыток для активностей
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(minutes=5),
            maximum_attempts=3,
            non_retryable_error_types=["ValueError", "KeyError"]
        )

        active_habits = await workflow.execute_activity(
            check_active_habits,
            retry_policy=retry_policy,
            start_to_close_timeout=timedelta(minutes=5),
        )
        if len(active_habits) == 0:
            return active_habits

        for active_habit in active_habits:
            try:
                await workflow.execute_activity(
                    update_illustrate_habit_quota,
                    retry_policy=retry_policy,
                    start_to_close_timeout=timedelta(minutes=5),
                    args=active_habit
                )
            except QuotaExceededException:
                continue

            completion_rate = await workflow.execute_activity(
                get_habit_completion_rate,
                retry_policy=retry_policy,
                start_to_close_timeout=timedelta(minutes=5),
                args=(active_habit.id, active_habit.interval)
            )

            await workflow.start_child_workflow(
                GenerateHabitImageWorkflow.run,
                (active_habit.user_id, active_habit.id, active_habit.text, completion_rate),
                id=f"generate_image_for_habit_{active_habit.id}",
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=10),
                    backoff_coefficient=2.0,
                    maximum_interval=timedelta(minutes=10),
                    maximum_attempts=5,  # Ограничиваем число попыток
                ),
                parent_close_policy=ParentClosePolicy.ABANDON,
            )


@workflow.defn
class GenerateHabitImageWorkflow:
    """
    Рабочий процесс для генерации изображений привычек
    """

    @workflow.run
    async def run(self, user_id: UUID, habit_id: UUID, habit_text: str, completion_rate: float):
        # Настраиваем политику повторных попыток для активностей
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(minutes=5),
            maximum_attempts=3,
            non_retryable_error_types=["ValueError", "KeyError"]
        )

        character = get_settings().HABIT_IMAGE_CHARACTER

        image_bytes, count_tokens = await workflow.execute_activity(
            generate_image,
            retry_policy=retry_policy,
            start_to_close_timeout=timedelta(minutes=10),
            args=(character, habit_text, completion_rate)
        )

        await workflow.execute_activity(
            update_describe_habit_text_quota,
            retry_policy=retry_policy,
            start_to_close_timeout=timedelta(minutes=5),
            args=(user_id, count_tokens)
        )

        image_url = await workflow.execute_activity(
            save_image_to_s3,
            retry_policy=retry_policy,
            start_to_close_timeout=timedelta(minutes=5),
            args=(user_id, image_bytes)
        )

        await workflow.execute_activity(
            save_image_to_db,
            retry_policy=retry_policy,
            start_to_close_timeout=timedelta(minutes=5),
            args=(user_id, habit_id, image_url)
        )
