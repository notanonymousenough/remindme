"""
Активности для работы с привычками
"""
import logging
from datetime import date, datetime, timedelta
from temporalio import activity
from typing import List, Dict, Any, Optional
from uuid import UUID

from app.db.engine import async_session
from app.db.repositories.habit import HabitRepository, HabitProgressRepository
from app.db.repositories.user import UserRepository
from app.db.repositories.statistics import UserStatisticsRepository
from app.db.models.base import HabitPeriod

logger = logging.getLogger("habit_activities")


@activity.defn
async def update_habit_streaks() -> int:
    """
    Обновляет серии всех активных привычек
    Возвращает количество обработанных привычек
    """
    logger.info("Обновление серий привычек")

    async with async_session() as session:
        habit_repo = HabitRepository(session)
        habit_progress_repo = HabitProgressRepository(session)

        # Получаем все активные привычки
        habits = await habit_repo.get_all_active()
        processed_count = 0

        for habit in habits:
            # Рассчитываем текущую серию
            current_streak = await habit_progress_repo.get_streak(habit.id)

            # Если текущая серия лучше предыдущей лучшей - обновляем лучшую
            best_streak = max(current_streak, habit.best_streak) if habit.best_streak else current_streak

            # Обновляем привычку
            await habit_repo.update_streaks(habit.id, current_streak, best_streak)
            processed_count += 1

        return processed_count


@activity.defn
async def process_habit_progress(
        habit_id: str,
        user_id: str,
        completed: bool,
        target_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Обрабатывает прогресс выполнения привычки
    """
    logger.info(f"Обработка прогресса привычки {habit_id}")

    if target_date:
        progress_date = date.fromisoformat(target_date)
    else:
        progress_date = date.today()

    async with async_session() as session:
        habit_repo = HabitRepository(session)
        habit_progress_repo = HabitProgressRepository(session)
        user_stats_repo = UserStatisticsRepository(session)

        # Получаем привычку
        habit = await habit_repo.get(UUID(habit_id))
        if not habit:
            logger.warning(f"Привычка {habit_id} не найдена")
            return {"success": False}

        # Отмечаем прогресс
        progress = await habit_progress_repo.mark_completed(UUID(habit_id), progress_date, completed)

        # Рассчитываем дни выполнения за текущий период
        period_dates = await habit_repo.calculate_period_dates(habit, progress_date)
        completed_days = await habit_progress_repo.count_completed_days(
            UUID(habit_id),
            period_dates["start"],
            period_dates["end"]
        )

        # Обновляем прогресс привычки
        total_days = (period_dates["end"] - period_dates["start"]).days + 1
        progress_percent = min(100, int((completed_days / total_days) * 100))
        await habit_repo.update_progress(UUID(habit_id), progress_percent)

        # Обновляем серию
        current_streak = await habit_progress_repo.get_streak(UUID(habit_id))
        best_streak = max(current_streak, habit.best_streak) if habit.best_streak else current_streak
        await habit_repo.update_streaks(UUID(habit_id), current_streak, best_streak)

        # Обновляем статистику пользователя, если привычка была выполнена
        if completed:
            await user_stats_repo.ensure_statistics(UUID(user_id))
            await user_stats_repo.increment_daily_activity(UUID(user_id), progress_date)

        return {
            "success": True,
            "habit_id": habit_id,
            "completed_days": completed_days,
            "total_days": total_days,
            "progress_percent": progress_percent,
            "current_streak": current_streak,
            "best_streak": best_streak
        }
