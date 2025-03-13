"""
Рабочие процессы для интеграций
"""
import logging
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from typing import Dict, Any

with workflow.unsafe.imports_passed_through():
    from ..activities.calendar_activities import sync_calendar_events
    import logging

logger = logging.getLogger("integration_workflows")


@workflow.defn
class SyncCalendarWorkflow:
    """
    Рабочий процесс для синхронизации календаря
    """

    @workflow.run
    async def run(self, user_id: str) -> Dict[str, Any]:
        # Настраиваем политику повторных попыток для активностей
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=5),
            maximum_interval=timedelta(minutes=10),
            maximum_attempts=3
        )

        # Синхронизируем календарь
        result = await workflow.execute_activity(
            sync_calendar_events,
            retry_policy=retry_policy,
            start_to_close_timeout=timedelta(minutes=10),
            args=[user_id]
        )

        return result
