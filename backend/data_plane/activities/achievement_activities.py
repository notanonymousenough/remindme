"""
Активности для работы с достижениями
"""
import logging
from datetime import datetime
from temporalio import activity
from typing import List, Dict, Any
from uuid import UUID

from app.db.engine import async_session
from app.db.repositories.user import UserRepository
from app.db.repositories.achievement import AchievementTemplateRepository, UserAchievementRepository
from app.db.repositories.reminder import ReminderRepository
from app.db.repositories.habit import HabitRepository, HabitProgressRepository
from app.db.repositories.tag import TagRepository
from app.db.models.base import AchievementCategory

logger = logging.getLogger("achievement_activities")


@activity.defn
async def process_user_achievements(user_id: str) -> Dict[str, Any]:
    """
    Проверяет и обновляет достижения пользователя
    """
    logger.info(f"Обработка достижений пользователя {user_id}")

    async with async_session() as session:
        user_repo = UserRepository(session)
        achievement_template_repo = AchievementTemplateRepository(session)
        user_achievement_repo = UserAchievementRepository(session)
        reminder_repo = ReminderRepository(session)
        habit_repo = HabitRepository(session)
        habit_progress_repo = HabitProgressRepository(session)
        tag_repo = TagRepository(session)

        # Получаем пользователя
        user = await user_repo.get(UUID(user_id))
        if not user:
            logger.warning(f"Пользователь {user_id} не найден")
            return {"success": False, "error": "Пользователь не найден"}

        # Убеждаемся, что у пользователя есть записи для всех шаблонов достижений
        await user_achievement_repo.ensure_user_achievements(UUID(user_id))

        # Получаем все достижения пользователя
        user_achievements = await user_achievement_repo.get_by_user(UUID(user_id))

        # Список разблокированных достижений в этом запуске
        newly_unlocked = []

        # Обрабатываем каждое достижение
        for achievement in user_achievements:
            # Пропускаем уже разблокированные достижения
            if achievement.unlocked:
                continue

            # Получаем шаблон достижения
            template = await achievement_template_repo.get(achievement.template_id)
            if not template:
                continue

            # Проверяем условия достижения в зависимости от категории
            if template.category == AchievementCategory.REMINDER:
                await process_reminder_achievement(
                    user_id=UUID(user_id),
                    achievement=achievement,
                    template=template,
                    reminder_repo=reminder_repo,
                    user_achievement_repo=user_achievement_repo,
                    newly_unlocked=newly_unlocked
                )

            elif template.category == AchievementCategory.HABIT:
                await process_habit_achievement(
                    user_id=UUID(user_id),
                    achievement=achievement,
                    template=template,
                    habit_repo=habit_repo,
                    habit_progress_repo=habit_progress_repo,
                    user_achievement_repo=user_achievement_repo,
                    newly_unlocked=newly_unlocked
                )

            elif template.category == AchievementCategory.SYSTEM:
                await process_system_achievement(
                    user_id=UUID(user_id),
                    achievement=achievement,
                    template=template,
                    user=user,
                    tag_repo=tag_repo,
                    user_achievement_repo=user_achievement_repo,
                    newly_unlocked=newly_unlocked
                )

        return {
            "success": True,
            "processed": len(user_achievements),
            "newly_unlocked": newly_unlocked
        }


async def process_reminder_achievement(
        user_id: UUID,
        achievement: Any,
        template: Any,
        reminder_repo: ReminderRepository,
        user_achievement_repo: UserAchievementRepository,
        newly_unlocked: List[str]
):
    """Обрабатывает достижения, связанные с напоминаниями"""

    # Получаем количество созданных напоминаний
    total_reminders = await reminder_repo.count(user_id=user_id)

    # Получаем количество выполненных напоминаний
    completed_reminders = await reminder_repo.count_completed(user_id=user_id)

    # Разбираемся с условием достижения
    condition_text = template.condition.lower()

    # Для первого напоминания
    if "первое напоминание" in condition_text and total_reminders > 0:
        await user_achievement_repo.unlock(achievement.id)
        newly_unlocked.append(template.name)

    # Для создания определенного количества напоминаний
    if "создать" in condition_text and "напоминани" in condition_text:
        # Ищем число в условии
        import re
        numbers = re.findall(r'\d+', condition_text)
        if numbers:
            target_count = int(numbers[0])
            if total_reminders >= target_count:
                await user_achievement_repo.unlock(achievement.id)
                newly_unlocked.append(template.name)
            else:
                # Обновляем прогресс
                progress = min(100, int((total_reminders / target_count) * 100))
                await user_achievement_repo.update_progress(achievement.id, progress)

    # Для выполнения определенного количества напоминаний
    if "выполни" in condition_text and "напоминани" in condition_text:
        # Ищем число в условии
        import re
        numbers = re.findall(r'\d+', condition_text)
        if numbers:
            target_count = int(numbers[0])
            if completed_reminders >= target_count:
                await user_achievement_repo.unlock(achievement.id)
                newly_unlocked.append(template.name)
            else:
                # Обновляем прогресс
                progress = min(100, int((completed_reminders / target_count) * 100))
                await user_achievement_repo.update_progress(achievement.id, progress)


async def process_habit_achievement(
        user_id: UUID,
        achievement: Any,
        template: Any,
        habit_repo: HabitRepository,
        habit_progress_repo: HabitProgressRepository,
        user_achievement_repo: UserAchievementRepository,
        newly_unlocked: List[str]
):
    """Обрабатывает достижения, связанные с привычками"""

    # Получаем количество созданных привычек
    total_habits = await habit_repo.count(user_id=user_id)

    # Получаем привычку с наибольшей серией
    best_streak_habit = await habit_repo.get_with_best_streak(user_id=user_id)
    best_streak = best_streak_habit.best_streak if best_streak_habit else 0

    # Разбираемся с условием достижения
    condition_text = template.condition.lower()

    # Для первой привычки
    if "первую привычку" in condition_text and total_habits > 0:
        await user_achievement_repo.unlock(achievement.id)
        newly_unlocked.append(template.name)

    # Для создания определенного количества привычек
    if "создать" in condition_text and "привыч" in condition_text:
        # Ищем число в условии
        import re
        numbers = re.findall(r'\d+', condition_text)
        if numbers:
            target_count = int(numbers[0])
            if total_habits >= target_count:
                await user_achievement_repo.unlock(achievement.id)
                newly_unlocked.append(template.name)
            else:
                # Обновляем прогресс
                progress = min(100, int((total_habits / target_count) * 100))
                await user_achievement_repo.update_progress(achievement.id, progress)

    # Для серии выполнения привычки
    if "подряд" in condition_text:
        # Ищем число в условии
        import re
        numbers = re.findall(r'\d+', condition_text)
        if numbers:
            target_streak = int(numbers[0])
            if best_streak >= target_streak:
                await user_achievement_repo.unlock(achievement.id)
                newly_unlocked.append(template.name)
            else:
                # Обновляем прогресс
                progress = min(100, int((best_streak / target_streak) * 100))
                await user_achievement_repo.update_progress(achievement.id, progress)


async def process_system_achievement(
        user_id: UUID,
        achievement: Any,
        template: Any,
        user: Any,
        tag_repo: TagRepository,
        user_achievement_repo: UserAchievementRepository,
        newly_unlocked: List[str]
):
    """Обрабатывает системные достижения"""

    # Получаем количество созданных тегов
    total_tags = await tag_repo.count(user_id=user_id)

    # Разбираемся с условием достижения
    condition_text = template.condition.lower()

    # Для создания определенного количества тегов
    if "тег" in condition_text:
        # Ищем число в условии
        import re
        numbers = re.findall(r'\d+', condition_text)
        if numbers:
            target_count = int(numbers[0])
            if total_tags >= target_count:
                await user_achievement_repo.unlock(achievement.id)
                newly_unlocked.append(template.name)
            else:
                # Обновляем прогресс
                progress = min(100, int((total_tags / target_count) * 100))
                await user_achievement_repo.update_progress(achievement.id, progress)

    # Для использования приложения определенное количество дней подряд
    if "дней подряд" in condition_text:
        # Ищем число в условии
        import re
        numbers = re.findall(r'\d+', condition_text)
        if numbers:
            target_streak = int(numbers[0])
            if user.streak >= target_streak:
                await user_achievement_repo.unlock(achievement.id)
                newly_unlocked.append(template.name)
            else:
                # Обновляем прогресс
                progress = min(100, int((user.streak / target_streak) * 100))
                await user_achievement_repo.update_progress(achievement.id, progress)
