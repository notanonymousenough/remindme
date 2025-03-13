"""
Рабочие процессы для статистики
"""
import logging
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from typing import Dict, Any

with workflow.unsafe.imports_passed_through():
    from ..activities.achievement_activities import process_user_achievements
    import logging

logger = logging.getLogger("statistic_workflows")


@workflow.defn
class UpdateUserStatisticsWorkflow:
    """
    Рабочий процесс для обновления статистики пользователя
    """

    @workflow.run
    async def run(self, user_id: str) -> Dict[str, Any]:
        # Настраиваем политику повторных попыток для активностей
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(minutes=5),
            maximum_attempts=3
        )

        # Обрабатываем достижения пользователя
        achievements_result = await workflow.execute_activity(
            process_user_achievements,
            retry_policy=retry_policy,
            start_to_close_timeout=timedelta(minutes=5),
            args=[user_id]
        )

        return {
            "user_id": user_id,
            "statistics_updated": True,
            "achievements_processed": achievements_result.get("processed", 0),
            "achievements_unlocked": len(achievements_result.get("newly_unlocked", []))
        }
