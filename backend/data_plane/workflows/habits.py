"""
Рабочие процессы для обработки привычек
"""
import asyncio
import logging
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from typing import List, Dict, Any

from temporalio.exceptions import ActivityError
from temporalio.workflow import ParentClosePolicy

with workflow.unsafe.imports_passed_through():
    from backend.data_plane.activities.habits import (
        check_active_habits,
        generate_image,
        save_image_to_s3,
        save_image_url_to_db
)
    import logging

logger = logging.getLogger("habit_workflows")


@workflow.defn
class StartImagesGenerationWorkflow:
    """
    Рабочий процесс для инициализации генерации изображений
    """

    @workflow.run
    async def run(self, iteration: int = 0):
        # Настраиваем политику повторных попыток для активностей
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(minutes=5),
            maximum_attempts=3,
            non_retryable_error_types=["ValueError", "KeyError"]
        )

        habit_images = await workflow.execute_activity(
            check_active_habits,
            retry_policy=retry_policy,
            start_to_close_timeout=timedelta(minutes=5),
        )
        if len(habit_images) == 0:
            return habit_images

        for habit_image in habit_images:
            await workflow.start_child_workflow(
                GenerateHabitImageWorkflow.run,
                habit_image,
                id=f"generate_image_for_habit_{habit_images['habit'].id}",
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=10),
                    backoff_coefficient=2.0,
                    maximum_interval=timedelta(minutes=10),
                    maximum_attempts=5,  # Ограничиваем число попыток
                ),
                parent_close_policy=ParentClosePolicy.ABANDON,
            )

        workflow.continue_as_new(iteration + 1)


@workflow.defn
class GenerateHabitImageWorkflow:
    """
    Рабочий процесс для генерации изображений привычек
    """

    @workflow.run
    async def run(self, image: dict):
        # Настраиваем политику повторных попыток для активностей
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(minutes=5),
            maximum_attempts=3,
            non_retryable_error_types=["ValueError", "KeyError"]
        )

        image_bytes = await workflow.execute_activity(
            generate_image,
            retry_policy=retry_policy,
            start_to_close_timeout=timedelta(minutes=5),
            args=image
        )

        image_url = await workflow.execute_activity(
            save_image_to_s3,
            retry_policy=retry_policy,
            start_to_close_timeout=timedelta(minutes=5),
            args=image_bytes
        )

        await workflow.execute_activity(
            save_image_url_to_db,
            retry_policy=retry_policy,
            start_to_close_timeout=timedelta(minutes=5),
            args=(image, image_url)
        )
