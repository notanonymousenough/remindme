"""
Рабочие процессы для обслуживания
"""
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from typing import Dict, Any

from backend.config import get_settings

with workflow.unsafe.imports_passed_through():
    from backend.data_plane.activities.maintenance import (
        get_removed_habits,
        get_removed_reminders,
        delete_habits,
        delete_reminders
    )
    import logging

logger = logging.getLogger("habit_workflows")


@workflow.defn
class CleanupRemovedItemsWorkflow:
    @workflow.run
    async def run(self) -> Dict[str, Any]:
        """
        Workflow that cleans up reminders and habits marked for removal.
        """
        # Get items marked for removal
        reminder_ids = await workflow.execute_activity(
            get_removed_reminders,
            start_to_close_timeout=timedelta(minutes=5)
        )

        habit_ids = await workflow.execute_activity(
            get_removed_habits,
            start_to_close_timeout=timedelta(minutes=5)
        )

        # Delete the items
        reminder_result = await workflow.execute_activity(
            delete_reminders,
            reminder_ids,
            start_to_close_timeout=timedelta(minutes=10)
        )

        habit_result = await workflow.execute_activity(
            delete_habits,
            habit_ids,
            start_to_close_timeout=timedelta(minutes=10)
        )

        # Return the results
        return {
            "reminders": {
                "found": len(reminder_ids),
                "deleted": reminder_result.get("count", 0),
                "success": reminder_result.get("success", False)
            },
            "habits": {
                "found": len(habit_ids),
                "deleted": habit_result.get("count", 0),
                "success": habit_result.get("success", False)
            }
        }

        # TODO: REMOVE OLD HabitProgress
        # TODO: REMOVE OLD UserQuotaUsage
        # TODO: REMOVE OLD UserRole

