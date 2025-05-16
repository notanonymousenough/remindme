"""
Рабочие процессы для обработки привычек
"""
import asyncio
import logging
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from typing import List, Dict, Any

with workflow.unsafe.imports_passed_through():
    from backend.data_plane.activities.morning import (
        check_today_habits,
        check_today_reminders,
        send_telegram_message,
        get_active_users
    )
    import logging

logger = logging.getLogger("morning_message_workflows")


@workflow.defn
class MorningMessageWorkflow:

    @workflow.run
    async def run(self, iteration: int = 0):
        # Настраиваем политику повторных попыток для активностей
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=10),
            maximum_attempts=5,  # Ограничиваем число попыток
        )

        user_ids = await workflow.execute_activity(
            get_active_users,
            retry_policy=retry_policy,
            schedule_to_close_timeout=timedelta(minutes=5)
        )

        for user_id in user_ids:
            # Проверяем активные напоминания
            reminders = await workflow.execute_activity(
                check_today_reminders,
                retry_policy=retry_policy,
                schedule_to_close_timeout=timedelta(minutes=5),
                args=[user_id]
            )
            # Проверяем активные привычки
            habits = await workflow.execute_activity(
                check_today_habits,
                retry_policy=retry_policy,
                schedule_to_close_timeout=timedelta(minutes=5),
                args=[user_id]
            )
            if len(reminders) > 0 or len(habits) > 0:
                # Высылаем сообщение
                await workflow.execute_activity(
                    send_telegram_message,
                    retry_policy=retry_policy,
                    schedule_to_close_timeout=timedelta(minutes=5),
                    args=[user_id, reminders, habits]
                )
