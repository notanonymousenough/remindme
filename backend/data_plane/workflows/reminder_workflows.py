"""
Рабочие процессы для обработки напоминаний
"""
import logging
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from typing import List, Dict, Any

with workflow.unsafe.imports_passed_through():
    from ..activities.reminder_activities import (
        check_active_reminders,
        mark_reminder_as_forgotten,
        send_telegram_notification
    )
    import logging

logger = logging.getLogger("reminder_workflows")


@workflow.defn
class CheckRemindersWorkflow:
    """
    Рабочий процесс для проверки активных напоминаний и отправки уведомлений
    """

    @workflow.run
    async def run(self) -> Dict[str, Any]:
        # Настраиваем политику повторных попыток для активностей
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(minutes=10),
            maximum_attempts=5,
            non_retryable_error_types=["ValueError", "KeyError"]
        )

        # Проверяем активные напоминания
        reminders = await workflow.execute_activity(
            check_active_reminders,
            retry_policy=retry_policy,
            start_to_close_timeout=timedelta(minutes=5)
        )

        # Для каждого напоминания запускаем процесс отправки уведомления
        for reminder in reminders:
            # Запускаем дочерний рабочий процесс для отправки уведомления
            await workflow.start_child_workflow(
                SendReminderNotificationWorkflow,
                reminder,
                id=f"send_reminder_{reminder['id']}",
                retry_policy=RetryPolicy(maximum_attempts=3)
            )

        return {
            "checked_reminders_count": len(reminders),
            "reminders_to_notify": len(reminders)
        }


@workflow.defn
class SendReminderNotificationWorkflow:
    """
    Рабочий процесс для отправки уведомления о напоминании
    """

    @workflow.run
    async def run(self, reminder: Dict[str, Any]) -> Dict[str, Any]:
        # Политика повторных попыток для отправки уведомлений
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(minutes=5),
            maximum_attempts=3
        )

        # Отправляем уведомление
        notification_sent = await workflow.execute_activity(
            send_telegram_notification,
            retry_policy=retry_policy,
            start_to_close_timeout=timedelta(minutes=2),
            args=[reminder["user_id"], reminder["id"], reminder["text"], reminder["time"]]
        )

        result = {
            "reminder_id": reminder["id"],
            "notification_sent": notification_sent
        }

        # Если не удалось отправить уведомление, помечаем напоминание как забытое
        if not notification_sent:
            # Ждем 10 минут после времени напоминания и проверяем его статус
            reminder_time = reminder["time"]

            await workflow.sleep(timedelta(minutes=10))

            # Помечаем напоминание как забытое, если оно не было выполнено
            await workflow.execute_activity(
                mark_reminder_as_forgotten,
                retry_policy=retry_policy,
                start_to_close_timeout=timedelta(minutes=1),
                args=[reminder["id"]]
            )

            result["marked_as_forgotten"] = True

        return result
