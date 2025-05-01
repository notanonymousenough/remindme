import logging
import json
from typing import Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.control_plane.db.types.roles import RoleType, ROLE_DESCRIPTIONS
from backend.control_plane.db.types.quotas import ResourceType, DEFAULT_QUOTAS, RESOURCE_DESCRIPTIONS
from backend.control_plane.db.types.achievements import (
    ACHIEVEMENT_DESCRIPTIONS, ACHIEVEMENT_CONDITIONS, ACHIEVEMENT_ICONS,
    ACHIEVEMENT_EXPERIENCE, ACHIEVEMENT_CATEGORIES
)
from backend.control_plane.db.models import Role, Quota, ResourceType as ResourceTypeModel, AchievementTemplate
from backend.control_plane.db.models.base import AchievementCategory

logger = logging.getLogger(__name__)


async def sync_roles_and_quotas(session: AsyncSession, dry_run: bool = False) -> Dict[str, Any]:
    """
    Синхронизирует роли, типы ресурсов и квоты в базе данных с определениями в модуле types.

    Args:
        session: Асинхронная сессия SQLAlchemy
        dry_run: Если True, только выводит изменения, без фактического применения

    Returns:
        Dict с информацией о внесенных изменениях
    """
    changes = {
        "roles": {
            "added": [],
            "updated": [],
            "unchanged": []
        },
        "resource_types": {
            "added": [],
            "updated": [],
            "unchanged": []
        },
        "quotas": {
            "added": [],
            "updated": [],
            "deleted": [],
            "unchanged": []
        }
    }

    # Получаем все существующие роли из БД
    stmt = select(Role)
    result = await session.execute(stmt)
    existing_roles = {role.name: role for role in result.scalars().all()}

    # Словарь для отслеживания ID ролей (нужен для работы с квотами)
    role_ids = {}

    # 1. Синхронизация ролей
    for role_type in RoleType:
        role_name = role_type.value
        description = ROLE_DESCRIPTIONS[role_type]

        if role_name in existing_roles:
            existing_role = existing_roles[role_name]
            role_ids[role_name] = existing_role.id

            # Проверяем, нужно ли обновлять описание
            if existing_role.description != description:
                if not dry_run:
                    existing_role.description = description
                    await session.flush()
                changes["roles"]["updated"].append({
                    "name": role_name,
                    "old_description": existing_role.description,
                    "new_description": description
                })
            else:
                changes["roles"]["unchanged"].append(role_name)
        else:
            # Создаем новую роль
            if not dry_run:
                new_role = Role(name=role_name, description=description)
                session.add(new_role)
                await session.flush()
                role_ids[role_name] = new_role.id
            changes["roles"]["added"].append({
                "name": role_name,
                "description": description
            })

    # 2. Синхронизация типов ресурсов
    stmt = select(ResourceTypeModel)
    result = await session.execute(stmt)
    existing_resource_types = {rt.name: rt for rt in result.scalars().all()}

    # Словарь для отслеживания ID типов ресурсов
    resource_type_ids = {}

    for resource_type in ResourceType:
        resource_name = resource_type.value
        description = RESOURCE_DESCRIPTIONS[resource_type]

        if resource_name in existing_resource_types:
            existing_rt = existing_resource_types[resource_name]
            resource_type_ids[resource_name] = existing_rt.id

            # Проверяем, нужно ли обновлять описание
            if existing_rt.description != description:
                if not dry_run:
                    existing_rt.description = description
                    await session.flush()
                changes["resource_types"]["updated"].append({
                    "name": resource_name,
                    "old_description": existing_rt.description,
                    "new_description": description
                })
            else:
                changes["resource_types"]["unchanged"].append(resource_name)
        else:
            # Создаем новый тип ресурса
            if not dry_run:
                new_rt = ResourceTypeModel(name=resource_name, description=description)
                session.add(new_rt)
                await session.flush()
                resource_type_ids[resource_name] = new_rt.id
            changes["resource_types"]["added"].append({
                "name": resource_name,
                "description": description
            })

    # Если это пробный запуск без созданных ID, возвращаем изменения
    if dry_run and not (role_ids and resource_type_ids):
        return changes

    # 3. Получаем все существующие квоты из БД
    stmt = select(Quota)
    result = await session.execute(stmt)
    existing_quotas: List[Quota] = list(result.scalars().all())

    # Создаем словарь для быстрого поиска квот
    quota_map = {}
    for quota in existing_quotas:
        role_name = None
        for name, rid in role_ids.items():
            if rid == quota.role_id:
                role_name = name
                break

        resource_name = None
        for name, rtid in resource_type_ids.items():
            if rtid == quota.resource_type_id:
                resource_name = name
                break

        if role_name and resource_name:
            key = f"{role_name}:{resource_name}"
            quota_map[key] = quota

    # 4. Синхронизация квот - добавляем/обновляем квоты из DEFAULT_QUOTAS
    expected_quotas = set()

    for role_name, quotas in DEFAULT_QUOTAS.items():
        if role_name not in role_ids and not dry_run:
            logger.warning(f"Роль {role_name} не найдена в базе данных, пропускаем квоты")
            continue

        role_id = role_ids.get(role_name)

        for resource_type, max_value in quotas.items():
            resource_name = resource_type.value

            if resource_name not in resource_type_ids and not dry_run:
                logger.warning(f"Тип ресурса {resource_name} не найден в базе данных, пропускаем квоту")
                continue

            resource_type_id = resource_type_ids.get(resource_name)
            expected_quotas.add(f"{role_name}:{resource_name}")

            quota_key = f"{role_name}:{resource_name}"
            if quota_key in quota_map:
                # Квота существует, проверяем значение
                quota = quota_map[quota_key]
                if quota.max_value != max_value:
                    if not dry_run:
                        quota.max_value = max_value
                        await session.flush()
                    changes["quotas"]["updated"].append({
                        "role": role_name,
                        "resource_type": resource_name,
                        "old_value": float(quota.max_value),
                        "new_value": float(max_value)
                    })
                else:
                    changes["quotas"]["unchanged"].append({
                        "role": role_name,
                        "resource_type": resource_name,
                        "value": float(max_value)
                    })
            else:
                # Добавляем новую квоту
                if not dry_run:
                    new_quota = Quota(
                        role_id=role_id,
                        resource_type_id=resource_type_id,
                        max_value=max_value
                    )
                    session.add(new_quota)
                    await session.flush()
                changes["quotas"]["added"].append({
                    "role": role_name,
                    "resource_type": resource_name,
                    "value": float(max_value)
                })

    # 5. Находим и удаляем квоты, которых нет в DEFAULT_QUOTAS
    for key, quota in quota_map.items():
        if key not in expected_quotas:
            role_name, resource_name = key.split(":", 1)
            if not dry_run:
                await session.delete(quota)
                await session.flush()
            changes["quotas"]["deleted"].append({
                "role": role_name,
                "resource_type": resource_name
            })


    achievement_changes = await sync_achievements(session, dry_run)
    changes["achievements"] = achievement_changes["achievements"]

    # Применяем изменения
    if not dry_run:
        await session.commit()

    return changes


async def sync_achievements(session: AsyncSession, dry_run: bool = False) -> Dict[str, Any]:
    """
    Синхронизирует шаблоны достижений в базе данных с определениями в модуле types.

    Args:
        session: Асинхронная сессия SQLAlchemy
        dry_run: Если True, только выводит изменения, без фактического применения

    Returns:
        Dict с информацией о внесенных изменениях
    """
    changes = {
        "achievements": {
            "added": [],
            "updated": [],
            "deleted": [],
            "unchanged": []
        }
    }

    # Получаем все существующие шаблоны достижений из БД
    stmt = select(AchievementTemplate)
    result = await session.execute(stmt)
    existing_achievements = {achievement.name: achievement for achievement in result.scalars().all()}

    # Создаем множество ожидаемых достижений для отслеживания удалений
    expected_achievements = set(ACHIEVEMENT_DESCRIPTIONS.keys())

    # Синхронизация достижений - добавление и обновление
    for achievement_name, description in ACHIEVEMENT_DESCRIPTIONS.items():
        icon_url = ACHIEVEMENT_ICONS.get(achievement_name, "")
        condition = json.dumps(ACHIEVEMENT_CONDITIONS.get(achievement_name, {}))
        category = ACHIEVEMENT_CATEGORIES.get(achievement_name, "SYSTEM")

        if achievement_name in existing_achievements:
            existing_achievement = existing_achievements[achievement_name]

            # Проверяем, нужно ли обновлять
            need_update = False
            updates = {}

            if existing_achievement.description != description:
                need_update = True
                updates["old_description"] = existing_achievement.description
                updates["new_description"] = description
                if not dry_run:
                    existing_achievement.description = description

            if existing_achievement.icon_url != icon_url:
                need_update = True
                updates["old_icon_url"] = existing_achievement.icon_url
                updates["new_icon_url"] = icon_url
                if not dry_run:
                    existing_achievement.icon_url = icon_url

            if existing_achievement.condition != condition:
                need_update = True
                updates["old_condition"] = existing_achievement.condition
                updates["new_condition"] = condition
                if not dry_run:
                    existing_achievement.condition = condition

            if existing_achievement.category != category:
                need_update = True
                updates["old_category"] = existing_achievement.category
                updates["new_category"] = category
                if not dry_run:
                    existing_achievement.category = category

            if need_update:
                if not dry_run:
                    await session.flush()
                changes["achievements"]["updated"].append({
                    "name": achievement_name,
                    **updates
                })
            else:
                changes["achievements"]["unchanged"].append(achievement_name)
        else:
            # Создаем новое достижение
            if not dry_run:
                new_achievement = AchievementTemplate(
                    name=achievement_name,
                    description=description,
                    icon_url=icon_url,
                    condition=condition,
                    category=category
                )
                session.add(new_achievement)
                await session.flush()

            changes["achievements"]["added"].append({
                "name": achievement_name,
                "description": description,
                "icon_url": icon_url,
                "condition": condition,
                "category": category
            })

    # Удаляем достижения, которых нет в определениях
    for name, achievement in existing_achievements.items():
        if name not in expected_achievements:
            if not dry_run:
                await session.delete(achievement)
                await session.flush()
            changes["achievements"]["deleted"].append(name)

    # Применяем изменения
    if not dry_run:
        await session.commit()

    return changes

