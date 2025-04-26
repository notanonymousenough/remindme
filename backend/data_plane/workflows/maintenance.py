"""
Рабочие процессы для обслуживания
"""
import logging
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from typing import Dict, Any

from backend.config import get_settings

with workflow.unsafe.imports_passed_through():
    pass

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
        days_threshold = get_settings().CLEANUP_DAYS_THRESHOLD

        # TODO: DELETE Removed Reminders
        # TODO: DELETE Removed Habits
        # TODO: REMOVE OLD HabitProgress
        # TODO: REMOVE OLD UserQuotaUsage
        # TODO: REMOVE OLD UserRole

        return {
            "days_threshold": days_threshold,
            "status": "completed"
        }
