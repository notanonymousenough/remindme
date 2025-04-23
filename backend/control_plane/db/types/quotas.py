from enum import Enum
from typing import Dict, List, Set

from .roles import RoleType
from backend.control_plane.clients.yandex_gpt.prompts import RequestType


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
    ResourceType.AI_PREDICT_REMINDER_TIME_DAILY: "Ежедневный лимит использования AI для предсказания времени (в рублях)",
    ResourceType.AI_PREDICT_REMINDER_TIME_MONTHLY: "Ежемесячный лимит использования AI для предсказания времени (в рублях)",
    ResourceType.ACTIVE_REMINDERS_COUNT: "Максимальное количество активных напоминаний",
    ResourceType.ACTIVE_HABITS_COUNT: "Максимальное количество активных привычек"
}

# Значения квот по умолчанию для разных ролей
DEFAULT_QUOTAS: Dict[str, Dict[ResourceType, float]] = {
    RoleType.BASIC.value: {
        ResourceType.AI_PREDICT_REMINDER_TIME_DAILY: 0.01,  # рубли
        ResourceType.AI_PREDICT_REMINDER_TIME_MONTHLY: 3,  # рубли
        ResourceType.ACTIVE_REMINDERS_COUNT: 1000,
        ResourceType.ACTIVE_HABITS_COUNT: 3
    },
    RoleType.PREMIUM.value: {
        ResourceType.AI_PREDICT_REMINDER_TIME_DAILY: 3.5,  # рубли
        ResourceType.AI_PREDICT_REMINDER_TIME_MONTHLY: 100,  # рубли
        ResourceType.ACTIVE_REMINDERS_COUNT: 100000,
        ResourceType.ACTIVE_HABITS_COUNT: 20
    },
    RoleType.ADMIN.value: {
        ResourceType.AI_PREDICT_REMINDER_TIME_DAILY: 50,  # рубли
        ResourceType.AI_PREDICT_REMINDER_TIME_MONTHLY: 1500,  # рубли
        ResourceType.ACTIVE_REMINDERS_COUNT: -1,
        ResourceType.ACTIVE_HABITS_COUNT: -1
    }
}

# Связь между типами запросов AI и необходимыми квотами
REQUEST_TYPE_TO_QUOTAS: Dict[RequestType, List[ResourceType]] = {
    RequestType.PREDICT_REMINDER_TIME: [
        ResourceType.AI_PREDICT_REMINDER_TIME_DAILY,
        ResourceType.AI_PREDICT_REMINDER_TIME_MONTHLY
    ]
}


def get_quotas_for_request_type(request_type: RequestType) -> List[ResourceType]:
    """
    Получить список типов ресурсов, необходимых для проверки квот для данного типа запроса

    Args:
        request_type: Тип запроса

    Returns:
        List[ResourceType]: Список типов ресурсов для проверки
    """
    return REQUEST_TYPE_TO_QUOTAS.get(request_type, [])
