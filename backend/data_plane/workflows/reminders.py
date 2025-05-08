"""
Рабочие процессы для обработки напоминаний
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
    from backend.data_plane.activities.reminders import (
        check_active_reminders,
        send_telegram_notification, abort_sent
)
    import logging

logger = logging.getLogger("reminder_workflows")


@workflow.defn
class CheckRemindersWorkflow:
    """
    Рабочий процесс для проверки активных напоминаний и отправки уведомлений
    """

    @workflow.run
    async def run(self, iteration: int = 0):
        # Настраиваем политику повторных попыток для активностей
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=10),
            maximum_attempts=5,  # Ограничиваем число попыток
        )

        # Проверяем активные напоминания
        reminders = await workflow.execute_activity(
            check_active_reminders,
            retry_policy=retry_policy,
            schedule_to_close_timeout=timedelta(minutes=5)
        )

        # Для каждого напоминания запускаем процесс отправки уведомления
        for reminder in reminders:
            # Запускаем дочерний рабочий процесс для отправки уведомления
            await workflow.start_child_workflow(
                SendReminderNotificationWorkflow.run,
                reminder,
                id=f"send_reminder_{reminder['id']}",
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=10),
                    backoff_coefficient=2.0,
                    maximum_interval=timedelta(minutes=10),
                    maximum_attempts=5,  # Ограничиваем число попыток
                ),
                parent_close_policy=ParentClosePolicy.ABANDON,
            )

        await asyncio.sleep(15)
        workflow.continue_as_new(iteration + 1)


@workflow.defn
class SendReminderNotificationWorkflow:
    """
    Рабочий процесс для отправки уведомления о напоминании
    """

    @workflow.run
    async def run(self, reminder: Dict[str, Any]):
        compensations = []  # Track compensation activities
        # Политика повторных попыток для отправки уведомлений
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=10),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=10),
            maximum_attempts=5,  # Ограничиваем число попыток
        )


        try:
            # Откат
            compensations.append(abort_sent)
            # Отправляем уведомление
            await workflow.execute_activity(
                send_telegram_notification,
                retry_policy=retry_policy,
                schedule_to_close_timeout=timedelta(minutes=5),
                args=[reminder["user_id"], reminder["id"], reminder["text"], reminder["time"]]
            )
        except ActivityError as e:
            workflow.logger.error("Activity failed: %s", e)
            for compensation_task in reversed(compensations):
                try:
                    await workflow.execute_activity(
                        compensation_task,
                        args=[reminder["id"]],
                        schedule_to_close_timeout=timedelta(minutes=5),
                        retry_policy=RetryPolicy(
                            initial_interval=timedelta(seconds=10),
                            backoff_coefficient=2.0,
                            maximum_interval=timedelta(hours=1),
                            maximum_attempts=0,  # Откатываем до последнего
                        )
                    )
                except ActivityError as comp_error:
                    workflow.logger.error("Compensation failed: %s", comp_error)
