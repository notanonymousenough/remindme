from enum import Enum
from typing import Dict

class RoleType(str, Enum):
    BASIC = "basic"
    PREMIUM = "premium"
    ADMIN = "admin"

# Описания ролей для удобства
ROLE_DESCRIPTIONS: Dict[RoleType, str] = {
    RoleType.BASIC: "Базовая роль с ограниченным доступом",
    RoleType.PREMIUM: "Премиум роль с расширенным доступом",
    RoleType.ADMIN: "Админская роль с полным доступом"
}

# Роль, назначаемая по умолчанию при отсутствии активной роли у пользователя
DEFAULT_ROLE = RoleType.BASIC
