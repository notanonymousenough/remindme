"""
Рабочие процессы для мониторинга
"""
import logging
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from typing import Dict, Any

from backend.config import get_settings

with workflow.unsafe.imports_passed_through():
    pass

logger = logging.getLogger("monitor_workflows")


@workflow.defn
class MonitorRemindersWorkflow:
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

        # TODO: мониторить прошедшие неотправленные напоминалки


@workflow.defn
class MonitorQuotasWorkflow:
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

        # TODO: мониторить использование квот пользователями
