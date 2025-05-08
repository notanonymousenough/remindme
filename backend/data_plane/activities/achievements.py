"""
Активности для работы с достижениями пользователей
"""
import logging
import json
from datetime import datetime, timezone, timedelta
from temporalio import activity
from typing import List, Dict, Any, Optional
from uuid import UUID

from backend.control_plane.db.repositories.reminder import ReminderRepository
from backend.control_plane.db.repositories.habit import HabitRepository
from backend.control_plane.db.repositories.user import UserRepository
from backend.control_plane.db.repositories.achievement import AchievementTemplateRepository, UserAchievementRepository
from backend.control_plane.db.models.base import AchievementCategory, ReminderStatus, HabitInterval
from backend.control_plane.db.types.achievements import (
    ReminderAchievementType,
    HabitAchievementType,
    SystemAchievementType,
    ACHIEVEMENT_CONDITIONS,
    ACHIEVEMENT_CATEGORIES,
    ACHIEVEMENT_EXPERIENCE
)
from backend.control_plane.utils import timeutils
from backend.data_plane.services.telegram_service import TelegramService

logger = logging.getLogger("achievement_activities")


@activity.defn
async def get_users_for_achievement_check() -> List[Dict[str, Any]]:
    """
    Получает список пользователей для проверки достижений
    """
    logger.info("Получение списка пользователей для проверки достижений")
    user_repo = UserRepository()

    # Получаем пользователей, которые были активны за последние 7 дней
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    users = await user_repo.get_all_models()

    # Формируем список активных пользователей
    users_data = []
    for user in users:
        # Проверяем, что пользователь был активен недавно
        if user.last_active and user.last_active >= one_week_ago:
            user_data = {
                "id": str(user.id),
                "username": user.username,
                "telegram_id": user.telegram_id,
                "level": user.level,
                "experience": user.experience,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_active": user.last_active.isoformat() if user.last_active else None,
                "streak": user.streak
            }
            users_data.append(user_data)

    return users_data


@activity.defn
async def check_user_achievements(user_id: str) -> List[Dict[str, Any]]:
    """
    Проверяет достижения пользователя и определяет, какие из них нужно выдать или обновить
    """
    logger.info(f"Проверка достижений для пользователя {user_id}")

    user_uuid = UUID(user_id)
    achievement_template_repo = AchievementTemplateRepository()
    user_achievement_repo = UserAchievementRepository()
    reminder_repo = ReminderRepository()
    #habit_repo = HabitRepository()
    user_repo = UserRepository()

    # Получаем пользователя для доступа к его данным
    user = await user_repo.get_by_model_id(user_uuid)
    if not user:
        logger.error(f"Пользователь {user_id} не найден")
        return []

    # Получаем все шаблоны достижений
    templates = await achievement_template_repo.get_all_models()

    # Получаем текущие достижения пользователя
    user_achievements = await user_achievement_repo.get_models(user_id=user_uuid)

    # Создаем словарь существующих достижений для быстрого доступа
    existing_achievements = {str(ua.template_id): ua for ua in user_achievements}

    # Результаты проверки достижений
    achievements_to_process = []

    # Статистика пользователя (кэшируем для избежания повторных запросов)
    user_stats = {
        "created_reminders": None,
        "completed_reminders": None,
        "completed_on_time": None,
        "created_habits": None,
        "daily_habits_streak": None,
        "weekly_habits_streak": None,
        "monthly_habits_streak": None,
        "active_days": None,
        "profile_complete": None
    }

    for template in templates:
        template_id = str(template.id)
        template_name = template.name
        conditions = json.loads(template.condition) if template.condition else {}
        category = template.category

        # Проверяем достижения в зависимости от категории
        if category == AchievementCategory.REMINDER:
            await _check_reminder_achievement(
                template_id, template_name, conditions, user_uuid,
                existing_achievements, achievements_to_process,
                reminder_repo, user_stats
            )
        # elif category == AchievementCategory.HABIT:
        #     await _check_habit_achievement(
        #         template_id, template_name, conditions, user_uuid,
        #         existing_achievements, achievements_to_process,
        #         habit_repo, user_stats
        #     )
        elif category == AchievementCategory.SYSTEM:
            await _check_system_achievement(
                template_id, template_name, conditions, user_uuid,
                existing_achievements, achievements_to_process,
                user, user_stats
            )

    return achievements_to_process


async def _check_reminder_achievement(
    template_id: str,
    template_name: str,
    conditions: Dict[str, Any],
    user_id: UUID,
    existing_achievements: Dict[str, Any],
    achievements_to_process: List[Dict[str, Any]],
    reminder_repo: ReminderRepository,
    user_stats: Dict[str, Any]
):
    """Проверяет достижения, связанные с напоминаниями"""

    # Проверяем достижения за создание напоминаний
    if "created_reminders" in conditions:
        required_count = conditions["created_reminders"]

        # Кэшируем результат, если еще не запрашивали
        if user_stats["created_reminders"] is None:
            user_stats["created_reminders"] = await reminder_repo.count_models(user_id=user_id)

        created_count = user_stats["created_reminders"]
        should_grant = created_count >= required_count
        await _process_achievement_status(
            template_id, should_grant, created_count, required_count,
            existing_achievements, achievements_to_process
        )

    # Проверяем достижения за выполнение напоминаний
    elif "completed_reminders" in conditions:
        required_count = conditions["completed_reminders"]

        # Кэшируем результат, если еще не запрашивали
        if user_stats["completed_reminders"] is None:
            user_stats["completed_reminders"] = await reminder_repo.count_models(
                user_id=user_id,
                status=ReminderStatus.COMPLETED
            )

        completed_count = user_stats["completed_reminders"]
        should_grant = completed_count >= required_count
        await _process_achievement_status(
            template_id, should_grant, completed_count, required_count,
            existing_achievements, achievements_to_process
        )

    # Проверяем достижения за выполнение напоминаний вовремя
    elif "completed_on_time" in conditions:
        required_count = conditions["completed_on_time"]

        # Кэшируем результат, если еще не запрашивали
        if user_stats["completed_on_time"] is None:
            # Здесь нужна дополнительная логика для определения выполненных вовремя напоминаний
            # Упрощенно предположим, что каждое выполненное напоминание было вовремя
            user_stats["completed_on_time"] = await reminder_repo.count_models(
                user_id=user_id,
                status=ReminderStatus.COMPLETED
            )

        on_time_count = user_stats["completed_on_time"]
        should_grant = on_time_count >= required_count
        await _process_achievement_status(
            template_id, should_grant, on_time_count, required_count,
            existing_achievements, achievements_to_process
        )

    # Проверяем достижения за серию напоминаний
    elif "daily_streak" in conditions:
        required_streak = conditions["daily_streak"]

        # Получаем текущую серию из профиля пользователя - это должно быть
        # реализовано в основной бизнес-логике приложения
        current_streak = user_stats.get("streak", 0)

        should_grant = current_streak >= required_streak
        await _process_achievement_status(
            template_id, should_grant, current_streak, required_streak,
            existing_achievements, achievements_to_process
        )


async def _check_habit_achievement(
    template_id: str,
    template_name: str,
    conditions: Dict[str, Any],
    user_id: UUID,
    existing_achievements: Dict[str, Any],
    achievements_to_process: List[Dict[str, Any]],
    habit_repo: HabitRepository,
    user_stats: Dict[str, Any]
):
    """Проверяет достижения, связанные с привычками"""

    # Проверяем достижения за создание привычек
    if "created_habits" in conditions:
        required_count = conditions["created_habits"]

        # Кэшируем результат, если еще не запрашивали
        if user_stats["created_habits"] is None:
            user_stats["created_habits"] = await habit_repo.count_models(user_id=user_id)

        created_count = user_stats["created_habits"]
        should_grant = created_count >= required_count
        await _process_achievement_status(
            template_id, should_grant, created_count, required_count,
            existing_achievements, achievements_to_process
        )

    # Проверяем достижения за серию ежедневных привычек
    elif "daily_habit_streak" in conditions:
        required_streak = conditions["daily_habit_streak"]

        # Кэшируем результат, если еще не запрашивали
        if user_stats["daily_habits_streak"] is None:
            # Здесь должна быть логика определения серии для ежедневных привычек
            # Упрощенно предположим, что серия равна 14 дням
            user_stats["daily_habits_streak"] = 14  # Заглушка, нужна настоящая имплементация

        daily_streak = user_stats["daily_habits_streak"]
        should_grant = daily_streak >= required_streak
        await _process_achievement_status(
            template_id, should_grant, daily_streak, required_streak,
            existing_achievements, achievements_to_process
        )

    # Проверяем достижения за серию еженедельных привычек
    elif "weekly_habit_streak" in conditions:
        required_streak = conditions["weekly_habit_streak"]

        # Кэшируем результат, если еще не запрашивали
        if user_stats["weekly_habits_streak"] is None:
            # Здесь должна быть логика определения серии для еженедельных привычек
            # Упрощенно предположим, что серия равна 8 неделям
            user_stats["weekly_habits_streak"] = 8  # Заглушка, нужна настоящая имплементация

        weekly_streak = user_stats["weekly_habits_streak"]
        should_grant = weekly_streak >= required_streak
        await _process_achievement_status(
            template_id, should_grant, weekly_streak, required_streak,
            existing_achievements, achievements_to_process
        )

    # Проверяем достижения за серию ежемесячных привычек
    elif "monthly_habit_streak" in conditions:
        required_streak = conditions["monthly_habit_streak"]

        # Кэшируем результат, если еще не запрашивали
        if user_stats["monthly_habits_streak"] is None:
            # Здесь должна быть логика определения серии для ежемесячных привычек
            # Упрощенно предположим, что серия равна 6 месяцам
            user_stats["monthly_habits_streak"] = 6  # Заглушка, нужна настоящая имплементация

        monthly_streak = user_stats["monthly_habits_streak"]
        should_grant = monthly_streak >= required_streak
        await _process_achievement_status(
            template_id, should_grant, monthly_streak, required_streak,
            existing_achievements, achievements_to_process
        )


async def _check_system_achievement(
    template_id: str,
    template_name: str,
    conditions: Dict[str, Any],
    user_id: UUID,
    existing_achievements: Dict[str, Any],
    achievements_to_process: List[Dict[str, Any]],
    user: Any,
    user_stats: Dict[str, Any]
):
    """Проверяет системные достижения"""

    # Проверяем достижение "Первопроходец"
    if "registered_before" in conditions:
        cutoff_date = datetime.fromisoformat(conditions["registered_before"]).date()
        registration_date = user.created_at.date()

        should_grant = registration_date <= cutoff_date
        # Для "Первопроходца" прогресс либо 0%, либо 100%
        progress = 100 if should_grant else 0
        required = 100

        await _process_achievement_status(
            template_id, should_grant, progress, required,
            existing_achievements, achievements_to_process
        )

    # Проверяем достижение "Заполненный профиль"
    elif "profile_fields_filled" in conditions:
        required_fields = conditions["profile_fields_filled"]

        # Кэшируем результат, если еще не запрашивали
        if user_stats["profile_complete"] is None:
            # Проверяем заполненность полей профиля
            filled_fields = 0
            for field in required_fields:
                if hasattr(user, field) and getattr(user, field) is not None:
                    filled_fields += 1

            user_stats["profile_complete"] = filled_fields

        filled_count = user_stats["profile_complete"]
        required_count = len(required_fields)
        should_grant = filled_count == required_count

        progress = int((filled_count / required_count) * 100) if required_count > 0 else 0

        await _process_achievement_status(
            template_id, should_grant, progress, 100,
            existing_achievements, achievements_to_process
        )

    # Проверяем достижение "Активный пользователь"
    elif "active_days" in conditions:
        required_days = conditions["active_days"]

        # Кэшируем результат, если еще не запрашивали
        if user_stats["active_days"] is None:
            # Вычисляем количество дней с момента регистрации
            registration_date = user.created_at
            now = datetime.now(timezone.utc)
            days_since_registration = (now - registration_date).days if registration_date else 0

            user_stats["active_days"] = days_since_registration

        active_days = user_stats["active_days"]
        should_grant = active_days >= required_days

        await _process_achievement_status(
            template_id, should_grant, active_days, required_days,
            existing_achievements, achievements_to_process
        )


async def _process_achievement_status(
    template_id: str,
    should_grant: bool,
    current_value: int,
    required_value: int,
    existing_achievements: Dict[str, Any],
    achievements_to_process: List[Dict[str, Any]]
):
    """
    Обрабатывает статус достижения - определяет необходимость выдачи или обновления прогресса
    """
    # Вычисляем процент прогресса
    progress = min(100, int((current_value / required_value) * 100) if required_value > 0 else 0)

    # Если достижение уже существует
    if template_id in existing_achievements:
        user_achievement = existing_achievements[template_id]

        # Если достижение еще не разблокировано и условие выполнено
        if not user_achievement.unlocked and should_grant:
            achievements_to_process.append({
                "template_id": template_id,
                "should_grant": True,
                "progress": 100  # Полный прогресс при выдаче
            })
        # Иначе просто обновляем прогресс (если он изменился)
        elif not user_achievement.unlocked and user_achievement.progress != progress:
            achievements_to_process.append({
                "template_id": template_id,
                "should_grant": False,
                "progress": progress
            })
    else:
        # Создаем новое достижение
        if should_grant:
            achievements_to_process.append({
                "template_id": template_id,
                "should_grant": True,
                "progress": 100  # Полный прогресс при выдаче
            })
        else:
            achievements_to_process.append({
                "template_id": template_id,
                "should_grant": False,
                "progress": progress
            })


@activity.defn
async def grant_achievement(user_id: str, template_id: str):
    """
    Выдает достижение пользователю и начисляет ему опыт
    """
    logger.info(f"Выдача достижения {template_id} пользователю {user_id}")

    user_uuid = UUID(user_id)
    template_uuid = UUID(template_id)

    user_achievement_repo = UserAchievementRepository()
    achievement_template_repo = AchievementTemplateRepository()
    user_repo = UserRepository()

    # Получаем пользователя и шаблон достижения
    user = await user_repo.get_by_model_id(user_uuid)
    template = await achievement_template_repo.get_by_model_id(template_uuid)

    if not user or not template:
        logger.error(f"Не удалось найти пользователя {user_id} или шаблон достижения {template_id}")
        return

    # Определяем опыт за достижение из типов
    experience_bonus = ACHIEVEMENT_EXPERIENCE.get(template.name, 50)  # Используем 50 как значение по умолчанию

    # Проверяем, существует ли уже связь пользователь-достижение
    existing_achievements = await user_achievement_repo.get_models(
        user_id=user_uuid,
        template_id=template_uuid
    )

    # Текущее время для отметки о разблокировке
    now = datetime.now(timezone.utc)

    if existing_achievements:
        # Обновляем существующее достижение
        user_achievement = existing_achievements[0]
        await user_achievement_repo.update_model(
            model_id=user_achievement.id,
            unlocked=True,
            unlocked_at=now,
            progress=100  # Полный прогресс
        )
    else:
        # Создаем новое достижение
        await user_achievement_repo.create(
            user_id=user_uuid,
            template_id=template_uuid,
            unlocked=True,
            unlocked_at=now,
            progress=100  # Полный прогресс
        )

    # Увеличиваем опыт пользователя
    new_experience = user.experience + experience_bonus

    # Обновляем пользователя с новым опытом
    await user_repo.update_model(
        model_id=user_uuid,
        experience=new_experience
    )

    # Отправляем уведомление пользователю через Telegram
    if user.telegram_id:
        telegram_service = TelegramService()
        message = (
            f"🏆 Поздравляем! Вы получили достижение:\n\n"
            f"*{template.name}*\n\n"
            f"{template.description}\n\n"
            f"+{experience_bonus} очков опыта!"
        )

        await telegram_service.send_message(
            user.telegram_id,
            message,
            parse_mode="Markdown"
        )


@activity.defn
async def update_achievement_progress(user_id: str, template_id: str, progress: int):
    """
    Обновляет прогресс достижения пользователя
    """
    logger.info(f"Обновление прогресса достижения {template_id} для пользователя {user_id}")

    user_uuid = UUID(user_id)
    template_uuid = UUID(template_id)

    user_achievement_repo = UserAchievementRepository()

    # Проверяем, существует ли уже связь пользователь-достижение
    existing_achievements = await user_achievement_repo.get_models(
        user_id=user_uuid,
        template_id=template_uuid
    )

    if existing_achievements:
        # Обновляем существующее достижение только если новый прогресс больше текущего
        user_achievement = existing_achievements[0]
        if user_achievement.progress < progress:
            await user_achievement_repo.update_model(
                model_id=user_achievement.id,
                progress=progress
            )
    else:
        # Создаем новое достижение с начальным прогрессом
        await user_achievement_repo.create(
            user_id=user_uuid,
            template_id=template_uuid,
            unlocked=False,
            progress=progress
        )
