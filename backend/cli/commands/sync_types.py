import asyncio
import click
import json
import logging

from backend.control_plane.db.engine import get_async_session
from backend.control_plane.db.types.sync import sync_roles_and_quotas

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option("--dry-run", is_flag=True, help="Показать планируемые изменения без применения")
@click.option("--json", "json_output", is_flag=True, help="Вывести результаты в формате JSON")
def sync_types(dry_run: bool, json_output: bool):
    """Синхронизирует типы ролей и квот в базе данных с определениями из модуля types."""

    async def run():
        async with get_async_session() as session:
            if dry_run:
                click.echo("СУХОЙ ЗАПУСК: изменения не будут применены")

            changes = await sync_roles_and_quotas(session, dry_run=dry_run)

            if json_output:
                click.echo(json.dumps(changes, indent=2, ensure_ascii=False))
            else:
                print_changes(changes)

            if not dry_run:
                click.echo("Синхронизация типов успешно завершена")

    asyncio.run(run())


def print_changes(changes):
    """Красиво выводит изменения в консоль"""
    click.echo("\n========== РОЛИ ==========")

    if changes["roles"]["added"]:
        click.echo("\n✅ Добавленные роли:")
        for role in changes["roles"]["added"]:
            click.echo(f"  - {role['name']}: {role['description']}")

    if changes["roles"]["updated"]:
        click.echo("\n🔄 Обновленные роли:")
        for role in changes["roles"]["updated"]:
            click.echo(f"  - {role['name']}: {role['old_description']} → {role['new_description']}")

    if changes["roles"]["unchanged"]:
        click.echo("\n✓ Без изменений:")
        for role_name in changes["roles"]["unchanged"]:
            click.echo(f"  - {role_name}")

    click.echo("\n========== ТИПЫ РЕСУРСОВ ==========")

    if changes["resource_types"]["added"]:
        click.echo("\n✅ Добавленные типы ресурсов:")
        for rt in changes["resource_types"]["added"]:
            click.echo(f"  - {rt['name']}: {rt['description']}")

    if changes["resource_types"]["updated"]:
        click.echo("\n🔄 Обновленные типы ресурсов:")
        for rt in changes["resource_types"]["updated"]:
            click.echo(f"  - {rt['name']}: {rt['old_description']} → {rt['new_description']}")

    if changes["resource_types"]["unchanged"]:
        click.echo("\n✓ Без изменений:")
        for rt_name in changes["resource_types"]["unchanged"]:
            click.echo(f"  - {rt_name}")

    click.echo("\n========== КВОТЫ ==========")

    if changes["quotas"]["added"]:
        click.echo("\n✅ Добавленные квоты:")
        for quota in changes["quotas"]["added"]:
            click.echo(f"  - {quota['role']}.{quota['resource_type']} = {quota['value']}")

    if changes["quotas"]["updated"]:
        click.echo("\n🔄 Обновленные квоты:")
        for quota in changes["quotas"]["updated"]:
            click.echo(f"  - {quota['role']}.{quota['resource_type']}: {quota['old_value']} → {quota['new_value']}")

    if changes["quotas"]["deleted"]:
        click.echo("\n❌ Удаленные квоты:")
        for quota in changes["quotas"]["deleted"]:
            click.echo(f"  - {quota['role']}.{quota['resource_type']}")

    if changes["quotas"]["unchanged"]:
        click.echo("\n✓ Без изменений:")
        for quota in changes["quotas"]["unchanged"]:
            click.echo(f"  - {quota['role']}.{quota['resource_type']} = {quota['value']}")

    click.echo("\n========== ДОСТИЖЕНИЯ ==========")

    if changes["achievements"]["added"]:
        click.echo("\n✅ Добавленные достижения:")
        for achievement in changes["achievements"]["added"]:
            click.echo(f"  - {achievement['name']}: {achievement['description']} (категория: {achievement['category']})")

    if changes["achievements"]["updated"]:
        click.echo("\n🔄 Обновленные достижения:")
        for achievement in changes["achievements"]["updated"]:
            click.echo(f"  - {achievement['name']}")
            if "old_description" in achievement:
                click.echo(f"    • Описание: {achievement['old_description']} → {achievement['new_description']}")
            if "old_icon_url" in achievement:
                click.echo(f"    • Иконка: {achievement['old_icon_url']} → {achievement['new_icon_url']}")
            if "old_condition" in achievement:
                click.echo(f"    • Условие: {achievement['old_condition']} → {achievement['new_condition']}")
            if "old_category" in achievement:
                click.echo(f"    • Категория: {achievement['old_category']} → {achievement['new_category']}")

    if changes["achievements"]["deleted"]:
        click.echo("\n❌ Удаленные достижения:")
        for achievement_name in changes["achievements"]["deleted"]:
            click.echo(f"  - {achievement_name}")

    if changes["achievements"]["unchanged"]:
        click.echo("\n✓ Без изменений:")
        for achievement_name in changes["achievements"]["unchanged"]:
            click.echo(f"  - {achievement_name}")
