from enum import Enum
from typing import Dict, Any

from .roles import RoleType


class ResourceType(Enum):
    # Ежедневные лимиты
    AI_PREDICT_REMINDER_TIME_DAILY = "ai_predict_reminder_time_daily"
    # Ежемесячные лимиты
    AI_PREDICT_REMINDER_TIME_MONTHLY = "ai_predict_reminder_time_monthly"
    # Постоянные лимиты
    ACTIVE_REMINDERS_COUNT = "active_reminders_count"
    ACTIVE_HABITS_COUNT = "active_habits_count"


# Описания типов ресурсов
RESOURCE_DESCRIPTIONS = {
    ResourceType.AI_PREDICT_REMINDER_TIME_DAILY: "Ежедневный лимит использования AI (в рублях)",
    ResourceType.AI_PREDICT_REMINDER_TIME_MONTHLY: "Ежемесячный лимит использования AI (в рублях)",
    ResourceType.ACTIVE_REMINDERS_COUNT: "Максимальное количество активных напоминаний",
    ResourceType.ACTIVE_HABITS_COUNT: "Максимальное количество активных привычек"
}


# Значения квот по умолчанию для разных ролей
DEFAULT_QUOTAS: Dict[str, Dict[ResourceType, float]] = {
    RoleType.BASIC.value: {
        ResourceType.AI_PREDICT_REMINDER_TIME_DAILY: 0.01, # рубли
        ResourceType.AI_PREDICT_REMINDER_TIME_MONTHLY: 3, # рубли
        ResourceType.ACTIVE_REMINDERS_COUNT: 1000,
        ResourceType.ACTIVE_HABITS_COUNT: 3
    },
    RoleType.PREMIUM.value: {
        ResourceType.AI_PREDICT_REMINDER_TIME_DAILY: 3.5, # рубли
        ResourceType.AI_PREDICT_REMINDER_TIME_MONTHLY: 100, # рубли
        ResourceType.ACTIVE_REMINDERS_COUNT: 100000,
        ResourceType.ACTIVE_HABITS_COUNT: 20
    },
    RoleType.ADMIN.value: {
        ResourceType.AI_PREDICT_REMINDER_TIME_DAILY: 50, # рубли
        ResourceType.AI_PREDICT_REMINDER_TIME_MONTHLY: 1500, # рубли
        ResourceType.ACTIVE_REMINDERS_COUNT: -1,
        ResourceType.ACTIVE_HABITS_COUNT: -1
    }
}
