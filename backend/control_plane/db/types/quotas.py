from enum import Enum
from typing import Dict, List, Set

from backend.config import get_settings
from backend.control_plane.db.types.roles import RoleType
from backend.control_plane.ai_clients.prompts import RequestType


class ResourceType(Enum):
    # Ежедневные лимиты AI для напоминаний
    AI_PREDICT_REMINDER_TIME_DAILY = "ai_predict_reminder_time_daily"
    # Ежемесячные лимиты AI для напоминаний
    AI_PREDICT_REMINDER_TIME_MONTHLY = "ai_predict_reminder_time_monthly"

    # Ежедневные лимиты генерации изображений
    AI_GENERATE_IMAGE_DAILY = "ai_generate_image_daily"
    # Ежемесячные лимиты генерации изображений
    AI_GENERATE_IMAGE_MONTHLY = "ai_generate_image_monthly"

    # Постоянные лимиты
    ACTIVE_REMINDERS_COUNT = "active_reminders_count"
    ACTIVE_HABITS_COUNT = "active_habits_count"


# Описания типов ресурсов
RESOURCE_DESCRIPTIONS = {
    ResourceType.AI_PREDICT_REMINDER_TIME_DAILY: "Ежедневный лимит использования AI для предсказания времени (в рублях)",
    ResourceType.AI_PREDICT_REMINDER_TIME_MONTHLY: "Ежемесячный лимит использования AI для предсказания времени (в рублях)",
    ResourceType.AI_GENERATE_IMAGE_DAILY: "Ежедневный лимит генерации изображений (в рублях)",
    ResourceType.AI_GENERATE_IMAGE_MONTHLY: "Ежемесячный лимит генерации изображений (в рублях)",
    ResourceType.ACTIVE_REMINDERS_COUNT: "Максимальное количество активных напоминаний",
    ResourceType.ACTIVE_HABITS_COUNT: "Максимальное количество активных привычек"
}

# Значения квот по умолчанию для разных ролей
DEFAULT_QUOTAS: Dict[str, Dict[ResourceType, float]] = {
    RoleType.BASIC.value: {
        ResourceType.AI_PREDICT_REMINDER_TIME_DAILY: 0.01,  # рубли
        ResourceType.AI_PREDICT_REMINDER_TIME_MONTHLY: 3,  # рубли
        ResourceType.AI_GENERATE_IMAGE_DAILY: 1 * get_settings().YANDEX_ART_MODEL_COST,  # рубли
        ResourceType.AI_GENERATE_IMAGE_MONTHLY: 3 * get_settings().YANDEX_ART_MODEL_COST,  # рубли (3 изображения в месяц)
        ResourceType.ACTIVE_REMINDERS_COUNT: 1000,
        ResourceType.ACTIVE_HABITS_COUNT: 3
    },
    RoleType.PREMIUM.value: {
        ResourceType.AI_PREDICT_REMINDER_TIME_DAILY: 3.5,  # рубли
        ResourceType.AI_PREDICT_REMINDER_TIME_MONTHLY: 100,  # рубли
        ResourceType.AI_GENERATE_IMAGE_DAILY: 5 * get_settings().YANDEX_ART_MODEL_COST,  # рубли (5 изображений в день)
        ResourceType.AI_GENERATE_IMAGE_MONTHLY: 20 * get_settings().YANDEX_ART_MODEL_COST,  # рубли (20 изображений в месяц)
        ResourceType.ACTIVE_REMINDERS_COUNT: 100000,
        ResourceType.ACTIVE_HABITS_COUNT: 20
    },
    RoleType.ADMIN.value: {
        ResourceType.AI_PREDICT_REMINDER_TIME_DAILY: 50,  # рубли
        ResourceType.AI_PREDICT_REMINDER_TIME_MONTHLY: 1500,  # рубли
        ResourceType.AI_GENERATE_IMAGE_DAILY: 20 * get_settings().YANDEX_ART_MODEL_COST,  # рубли (20 изображений в день)
        ResourceType.AI_GENERATE_IMAGE_MONTHLY: 600 * get_settings().YANDEX_ART_MODEL_COST,  # рубли (600 изображений в месяц)
        ResourceType.ACTIVE_REMINDERS_COUNT: -1,
        ResourceType.ACTIVE_HABITS_COUNT: -1
    }
}

# Связь между типами запросов AI и необходимыми квотами
REQUEST_TYPE_TO_QUOTAS: Dict[RequestType, List[ResourceType]] = {
    RequestType.PREDICT_REMINDER_TIME: [
        ResourceType.AI_PREDICT_REMINDER_TIME_DAILY,
        ResourceType.AI_PREDICT_REMINDER_TIME_MONTHLY
    ],
    RequestType.ILLUSTRATE_HABIT: [
        ResourceType.AI_GENERATE_IMAGE_DAILY,
        ResourceType.AI_GENERATE_IMAGE_MONTHLY
    ],
    RequestType.DESCRIBE_HABIT_TEXT: [
        ResourceType.AI_GENERATE_IMAGE_DAILY,
        ResourceType.AI_GENERATE_IMAGE_MONTHLY
    ],
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

if __name__ == '__main__':
    basic_count = 1000
    premium_count = 50
    admin_count = 1

    total_limit = 0

    basic_limit = 0
    for resource, limit in DEFAULT_QUOTAS[RoleType.BASIC.value].items():
        if resource.value.startswith("ai_"):
            basic_limit += limit
    premium_limit = 0
    for resource, limit in DEFAULT_QUOTAS[RoleType.PREMIUM.value].items():
        if resource.value.startswith("ai_"):
            premium_limit += limit
    admin_limit = 0
    for resource, limit in DEFAULT_QUOTAS[RoleType.ADMIN.value].items():
        if resource.value.startswith("ai_"):
            admin_limit += limit
    total_limit = basic_limit * basic_count + premium_limit * premium_count + admin_limit * admin_count
    total_no_admin_limit = basic_limit * basic_count + premium_limit * premium_count

    print("AI cost:")
    print("Basic (1):", basic_limit)
    print("Premium (1):", premium_limit)
    print("Admin (1):", admin_limit)
    print(f"Basic ({basic_count}):", basic_limit * basic_count)
    print(f"Premium ({premium_count}):", premium_limit * premium_count)
    print(f"Admin ({admin_count}):", admin_limit * admin_count)
    print("Total Basic + Premium:", total_no_admin_limit)
    print("Total:", total_limit)
