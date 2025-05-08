from enum import Enum
from typing import Dict, List, Any


# Типы достижений для каждой категории
class ReminderAchievementType(str, Enum):
    CREATOR_BEGINNER = "creator_beginner"  # Создал первые напоминания
    CREATOR_INTERMEDIATE = "creator_intermediate"  # Создал достаточное количество напоминаний
    CREATOR_MASTER = "creator_master"  # Создал много напоминаний
    FINISHER_BEGINNER = "finisher_beginner"  # Выполнил первые напоминания
    FINISHER_INTERMEDIATE = "finisher_intermediate"  # Выполнил достаточное количество напоминаний
    FINISHER_MASTER = "finisher_master"  # Выполнил много напоминаний
    PUNCTUAL = "punctual"  # Выполнил напоминания вовремя
    STREAK_WEEK = "streak_week"  # Серия выполнений напоминаний в течение недели
    STREAK_MONTH = "streak_month"  # Серия выполнений напоминаний в течение месяца


class HabitAchievementType(str, Enum):
    HABIT_BEGINNER = "habit_beginner"  # Создал первые привычки
    HABIT_INTERMEDIATE = "habit_intermediate"  # Создал несколько привычек
    HABIT_MASTER = "habit_master"  # Создал много привычек
    DAILY_STREAK = "daily_streak"  # Серия выполнений ежедневных привычек
    WEEKLY_STREAK = "weekly_streak"  # Серия выполнений еженедельных привычек
    MONTHLY_STREAK = "monthly_streak"  # Серия выполнений ежемесячных привычек


class SystemAchievementType(str, Enum):
    EARLY_ADOPTER = "early_adopter"  # Один из первых пользователей
    PROFILE_COMPLETE = "profile_complete"  # Заполнил профиль полностью
    POWER_USER = "power_user"  # Активно пользуется системой


# Описания достижений
ACHIEVEMENT_DESCRIPTIONS: Dict[str, str] = {
    # Reminder Achievements
    ReminderAchievementType.CREATOR_BEGINNER.value: "Организатор: создайте 5 напоминаний",
    ReminderAchievementType.CREATOR_INTERMEDIATE.value: "Планировщик: создайте 25 напоминаний",
    ReminderAchievementType.CREATOR_MASTER.value: "Мастер планирования: создайте 100 напоминаний",
    ReminderAchievementType.FINISHER_BEGINNER.value: "Исполнитель: выполните 10 напоминаний",
    ReminderAchievementType.FINISHER_INTERMEDIATE.value: "Ответственный: выполните 50 напоминаний",
    ReminderAchievementType.FINISHER_MASTER.value: "Герой продуктивности: выполните 200 напоминаний",
    ReminderAchievementType.PUNCTUAL.value: "Пунктуальность: выполните 20 напоминаний вовремя",
    ReminderAchievementType.STREAK_WEEK.value: "Недельный марафон: выполняйте напоминания 7 дней подряд",
    ReminderAchievementType.STREAK_MONTH.value: "Месячный марафон: выполняйте напоминания 30 дней подряд",

    # Habit Achievements
    HabitAchievementType.HABIT_BEGINNER.value: "Начинающий: создайте 3 привычки",
    HabitAchievementType.HABIT_INTERMEDIATE.value: "Преобразователь: создайте 10 привычек",
    HabitAchievementType.HABIT_MASTER.value: "Мастер привычек: создайте 20 привычек",
    HabitAchievementType.DAILY_STREAK.value: "Ежедневная рутина: выполняйте ежедневные привычки 14 дней подряд",
    HabitAchievementType.WEEKLY_STREAK.value: "Еженедельный ритуал: выполняйте еженедельные привычки 8 недель подряд",
    HabitAchievementType.MONTHLY_STREAK.value: "Ежемесячная традиция: выполняйте ежемесячные привычки 6 месяцев подряд",

    # System Achievements
    SystemAchievementType.EARLY_ADOPTER.value: "Первопроходец: один из первых пользователей системы",
    SystemAchievementType.PROFILE_COMPLETE.value: "Детализатор: заполните свой профиль полностью",
    SystemAchievementType.POWER_USER.value: "Эксперт: активно пользуетесь системой более 3 месяцев"
}

# Условия для достижений
ACHIEVEMENT_CONDITIONS: Dict[str, Dict[str, Any]] = {
    # Reminder Achievements
    ReminderAchievementType.CREATOR_BEGINNER.value: {"created_reminders": 5},
    ReminderAchievementType.CREATOR_INTERMEDIATE.value: {"created_reminders": 25},
    ReminderAchievementType.CREATOR_MASTER.value: {"created_reminders": 100},
    ReminderAchievementType.FINISHER_BEGINNER.value: {"completed_reminders": 10},
    ReminderAchievementType.FINISHER_INTERMEDIATE.value: {"completed_reminders": 50},
    ReminderAchievementType.FINISHER_MASTER.value: {"completed_reminders": 200},
    ReminderAchievementType.PUNCTUAL.value: {"completed_on_time": 20},
    ReminderAchievementType.STREAK_WEEK.value: {"daily_streak": 7},
    ReminderAchievementType.STREAK_MONTH.value: {"daily_streak": 30},

    # Habit Achievements
    HabitAchievementType.HABIT_BEGINNER.value: {"created_habits": 3},
    HabitAchievementType.HABIT_INTERMEDIATE.value: {"created_habits": 10},
    HabitAchievementType.HABIT_MASTER.value: {"created_habits": 20},
    HabitAchievementType.DAILY_STREAK.value: {"daily_habit_streak": 14},
    HabitAchievementType.WEEKLY_STREAK.value: {"weekly_habit_streak": 8},
    HabitAchievementType.MONTHLY_STREAK.value: {"monthly_habit_streak": 6},

    # System Achievements
    SystemAchievementType.EARLY_ADOPTER.value: {"registered_before": "2025-12-31"},
    SystemAchievementType.PROFILE_COMPLETE.value: {
        "profile_fields_filled": ["first_name", "last_name", "birth_date", "sex"]},
    SystemAchievementType.POWER_USER.value: {"active_days": 90}
}

# Иконки для достижений (пути к файлам)
ACHIEVEMENT_ICONS: Dict[str, str] = {
    # Reminder Achievements
    ReminderAchievementType.CREATOR_BEGINNER.value: "/icons/achievements/creator_beginner.png",
    ReminderAchievementType.CREATOR_INTERMEDIATE.value: "/icons/achievements/creator_intermediate.png",
    ReminderAchievementType.CREATOR_MASTER.value: "/icons/achievements/creator_master.png",
    ReminderAchievementType.FINISHER_BEGINNER.value: "/icons/achievements/finisher_beginner.png",
    ReminderAchievementType.FINISHER_INTERMEDIATE.value: "/icons/achievements/finisher_intermediate.png",
    ReminderAchievementType.FINISHER_MASTER.value: "/icons/achievements/finisher_master.png",
    ReminderAchievementType.PUNCTUAL.value: "/icons/achievements/punctual.png",
    ReminderAchievementType.STREAK_WEEK.value: "/icons/achievements/streak_week.png",
    ReminderAchievementType.STREAK_MONTH.value: "/icons/achievements/streak_month.png",

    # Habit Achievements
    HabitAchievementType.HABIT_BEGINNER.value: "/icons/achievements/habit_beginner.png",
    HabitAchievementType.HABIT_INTERMEDIATE.value: "/icons/achievements/habit_intermediate.png",
    HabitAchievementType.HABIT_MASTER.value: "/icons/achievements/habit_master.png",
    HabitAchievementType.DAILY_STREAK.value: "/icons/achievements/daily_streak.png",
    HabitAchievementType.WEEKLY_STREAK.value: "/icons/achievements/weekly_streak.png",
    HabitAchievementType.MONTHLY_STREAK.value: "/icons/achievements/monthly_streak.png",

    # System Achievements
    SystemAchievementType.EARLY_ADOPTER.value: "/icons/achievements/early_adopter.png",
    SystemAchievementType.PROFILE_COMPLETE.value: "/icons/achievements/profile_complete.png",
    SystemAchievementType.POWER_USER.value: "/icons/achievements/power_user.png"
}

# Опыт, получаемый за достижения
ACHIEVEMENT_EXPERIENCE: Dict[str, int] = {
    # Reminder Achievements
    ReminderAchievementType.CREATOR_BEGINNER.value: 50,
    ReminderAchievementType.CREATOR_INTERMEDIATE.value: 150,
    ReminderAchievementType.CREATOR_MASTER.value: 400,
    ReminderAchievementType.FINISHER_BEGINNER.value: 100,
    ReminderAchievementType.FINISHER_INTERMEDIATE.value: 250,
    ReminderAchievementType.FINISHER_MASTER.value: 500,
    ReminderAchievementType.PUNCTUAL.value: 200,
    ReminderAchievementType.STREAK_WEEK.value: 300,
    ReminderAchievementType.STREAK_MONTH.value: 700,

    # Habit Achievements
    HabitAchievementType.HABIT_BEGINNER.value: 100,
    HabitAchievementType.HABIT_INTERMEDIATE.value: 250,
    HabitAchievementType.HABIT_MASTER.value: 500,
    HabitAchievementType.DAILY_STREAK.value: 400,
    HabitAchievementType.WEEKLY_STREAK.value: 450,
    HabitAchievementType.MONTHLY_STREAK.value: 650,

    # System Achievements
    SystemAchievementType.EARLY_ADOPTER.value: 200,
    SystemAchievementType.PROFILE_COMPLETE.value: 100,
    SystemAchievementType.POWER_USER.value: 500
}

# Категории достижений
ACHIEVEMENT_CATEGORIES: Dict[str, str] = {
    # Reminder Achievements
    ReminderAchievementType.CREATOR_BEGINNER.value: "REMINDER",
    ReminderAchievementType.CREATOR_INTERMEDIATE.value: "REMINDER",
    ReminderAchievementType.CREATOR_MASTER.value: "REMINDER",
    ReminderAchievementType.FINISHER_BEGINNER.value: "REMINDER",
    ReminderAchievementType.FINISHER_INTERMEDIATE.value: "REMINDER",
    ReminderAchievementType.FINISHER_MASTER.value: "REMINDER",
    ReminderAchievementType.PUNCTUAL.value: "REMINDER",
    ReminderAchievementType.STREAK_WEEK.value: "REMINDER",
    ReminderAchievementType.STREAK_MONTH.value: "REMINDER",

    # Habit Achievements
    HabitAchievementType.HABIT_BEGINNER.value: "HABIT",
    HabitAchievementType.HABIT_INTERMEDIATE.value: "HABIT",
    HabitAchievementType.HABIT_MASTER.value: "HABIT",
    HabitAchievementType.DAILY_STREAK.value: "HABIT",
    HabitAchievementType.WEEKLY_STREAK.value: "HABIT",
    HabitAchievementType.MONTHLY_STREAK.value: "HABIT",

    # System Achievements
    SystemAchievementType.EARLY_ADOPTER.value: "SYSTEM",
    SystemAchievementType.PROFILE_COMPLETE.value: "SYSTEM",
    SystemAchievementType.POWER_USER.value: "SYSTEM"
}
