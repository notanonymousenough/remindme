"""
Активности для обслуживания
"""
import logging
import asyncio
from datetime import datetime, timedelta
from pyexpat.errors import messages

from temporalio import activity
from typing import List, Dict, Any
from uuid import UUID

from backend.bot.routers.start import habits
from backend.control_plane.db.repositories.habit import HabitRepository
from backend.control_plane.db.repositories.reminder import ReminderRepository

logger = logging.getLogger("morning_message_activities")

@activity.defn
async def get_removed_reminders() -> List[str]:
    """
    Returns IDs of reminders marked for removal.
    """
    logger.info("Fetching reminders marked for removal")
    try:
        reminders_repo = ReminderRepository()
        removed_reminders = await reminders_repo.get_all_models(removed=True)
        return [rr.id for rr in removed_reminders]
    except Exception as e:
        logger.error(f"Error fetching removed reminders: {str(e)}")
        return []


@activity.defn
async def get_removed_habits() -> List[str]:
    """
    Returns IDs of habits marked for removal.
    """
    logger.info("Fetching habits marked for removal")
    try:
        habits_repo = HabitRepository()
        removed_habits = await habits_repo.get_all_models(removed=True)
        return [rh.id for rh in removed_habits]
    except Exception as e:
        logger.error(f"Error fetching removed habits: {str(e)}")
        return []


@activity.defn
async def delete_reminders(reminder_ids: List[UUID]) -> Dict[str, Any]:
    """
    Permanently deletes reminders with the given IDs.
    """
    if not reminder_ids:
        return {"count": 0, "success": True}

    logger.info(f"Deleting {len(reminder_ids)} reminders")
    try:
        # Delete in batches to avoid overwhelming the database
        batch_size = 100
        deleted_count = 0

        reminders_repo = ReminderRepository()

        for i in range(0, len(reminder_ids), batch_size):
            batch_ids = reminder_ids[i:i + batch_size]
            await reminders_repo.delete_models(batch_ids)
            deleted_count += batch_size

        logger.info(f"Successfully deleted {deleted_count} reminders")
        return {"count": deleted_count, "success": True}
    except Exception as e:
        logger.error(f"Error deleting reminders: {str(e)}")
        return {"count": 0, "success": False, "error": str(e)}


@activity.defn
async def delete_habits(habit_ids: List[UUID]) -> Dict[str, Any]:
    """
    Permanently deletes habits with the given IDs.
    """
    if not habit_ids:
        return {"count": 0, "success": True}

    logger.info(f"Deleting {len(habit_ids)} habits")
    try:
        # Delete in batches to avoid overwhelming the database
        batch_size = 100
        deleted_count = 0

        habits_repo = HabitRepository()

        for i in range(0, len(habit_ids), batch_size):
            batch_ids = habit_ids[i:i + batch_size]
            await habits_repo.delete_models(batch_ids)
            deleted_count += batch_size

        logger.info(f"Successfully deleted {deleted_count} habits")
        return {"count": deleted_count, "success": True}
    except Exception as e:
        logger.error(f"Error deleting habits: {str(e)}")
        return {"count": 0, "success": False, "error": str(e)}
