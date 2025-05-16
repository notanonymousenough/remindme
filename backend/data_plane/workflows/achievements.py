"""
Рабочие процессы для обработки достижений пользователей
"""
import asyncio
import logging
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from typing import List, Dict, Any, Optional

from temporalio.exceptions import ActivityError
from temporalio.workflow import ParentClosePolicy

from backend.control_plane.utils import timeutils

with workflow.unsafe.imports_passed_through():
    from backend.data_plane.activities.achievements import (
        get_users_for_achievement_check,
        check_user_achievements,
        grant_achievement,
        update_achievement_progress
    )
    import logging

logger = logging.getLogger("achievement_workflows")


@workflow.defn
class CheckUserAchievementsWorkflow:
    """
    Рабочий процесс для периодической проверки и выдачи достижений пользователям
    """

    @workflow.run
    async def run(self):
        # Настраиваем политику повторных попыток для активностей
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=10),
            maximum_attempts=5,
        )

        # Получаем список пользователей для проверки достижений
        users = await workflow.execute_activity(
            get_users_for_achievement_check,
            retry_policy=retry_policy,
            schedule_to_close_timeout=timedelta(minutes=5)
        )

        # Для каждого пользователя запускаем проверку достижений
        for user in users:
            await workflow.start_child_workflow(
                ProcessUserAchievementsWorkflow.run,
                user,
                id=f"process_achievements_{user['id']}",
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=10),
                    backoff_coefficient=2.0,
                    maximum_interval=timedelta(minutes=10),
                    maximum_attempts=3,
                ),
                parent_close_policy=ParentClosePolicy.ABANDON,
            )


@workflow.defn
class ProcessUserAchievementsWorkflow:
    """
    Рабочий процесс для проверки и выдачи достижений конкретному пользователю
    """

    @workflow.run
    async def run(self, user: Dict[str, Any]):
        # Политика повторных попыток
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=10),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=10),
            maximum_attempts=3,
        )

        # Проверяем достижения пользователя
        achievements_to_process = await workflow.execute_activity(
            check_user_achievements,
            args=[user["id"]],
            retry_policy=retry_policy,
            schedule_to_close_timeout=timedelta(minutes=5)
        )

        # Обрабатываем каждое достижение
        for achievement in achievements_to_process:
            if achievement["should_grant"]:
                # Выдаем достижение
                await workflow.execute_activity(
                    grant_achievement,
                    args=[user["id"], achievement["template_id"]],
                    retry_policy=retry_policy,
                    schedule_to_close_timeout=timedelta(minutes=5)
                )
            else:
                # Обновляем прогресс достижения
                await workflow.execute_activity(
                    update_achievement_progress,
                    args=[user["id"], achievement["template_id"], achievement["progress"]],
                    retry_policy=retry_policy,
                    schedule_to_close_timeout=timedelta(minutes=5)
                )
