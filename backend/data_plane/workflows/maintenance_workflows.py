"""
Рабочие процессы для обслуживания
"""
import logging
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from typing import Dict, Any

with workflow.unsafe.imports_passed_through():
    import logging
    from ..config import settings

logger = logging.getLogger("maintenance_workflows")


@workflow.defn
class CleanupRemovedItemsWorkflow:
    """
    Рабочий процесс для очистки удаленных напоминаний и привычек
    """

    @workflow.run
    async def run(self) -> Dict[str, Any]:
        # Настраиваем политику повторных попыток для активностей
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(minutes=10),
            maximum_attempts=3
        )

        # Определяем порог дней для очистки
        days_threshold = settings.CLEANUP_DAYS_THRESHOLD

        # Очищаем удаленные напоминания
        await workflow.execute_activity(
            "cleanup_removed_reminders",
            retry_policy=retry_policy,
            start_to_close_timeout=timedelta(minutes=30),
            args=[days_threshold]
        )

        # Очищаем удаленные привычки
        await workflow.execute_activity(
            "cleanup_removed_habits",
            retry_policy=retry_policy,
            start_to_close_timeout=timedelta(minutes=30),
            args=[days_threshold]
        )

        return {
            "days_threshold": days_threshold,
            "status": "completed"
        }
